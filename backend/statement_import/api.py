"""
Statement Import Blueprint

  POST   /api/import/statement/preview   multipart: file, password (optional)
  POST   /api/import/statement/confirm   JSON: {rows: [...]} (rows from preview, edited)
  GET    /api/import/transactions        ?month=YYYY-MM
  GET    /api/import/recurring           detected recurring payments/income + monthly totals
  DELETE /api/import/batch/<batch_id>    undo one import

Uploaded files are read into memory and discarded; neither the file nor a
PDF password is stored or logged.
"""

import logging

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from db_core import get_db
from statement_import import service
from statement_import.parser import SUPPORTED_EXTENSIONS, StatementParseError, StatementPasswordRequired

logger = logging.getLogger(__name__)

statement_import_bp = Blueprint("statement_import", __name__, url_prefix="/api/import")


@statement_import_bp.route("/statement/preview", methods=["POST"])
@jwt_required()
def preview_statement():
    upload = request.files.get("file")
    if upload is None or not upload.filename:
        return jsonify({"success": False, "error": "No file uploaded"}), 400
    if not upload.filename.lower().endswith(SUPPORTED_EXTENSIONS):
        return jsonify({"success": False, "error": "Upload a CSV, XLS, XLSX or PDF statement"}), 400

    data = upload.read()
    password = request.form.get("password") or None
    try:
        result = service.preview(get_db(), int(get_jwt_identity()), upload.filename, data, password)
    except StatementPasswordRequired as e:
        return jsonify({"success": False, "password_required": True, "error": str(e)}), 422
    except StatementParseError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    finally:
        del data, password
    return jsonify({"success": True, **result})


@statement_import_bp.route("/statement/confirm", methods=["POST"])
@jwt_required()
def confirm_statement():
    body = request.get_json(silent=True) or {}
    rows = body.get("rows")
    if not isinstance(rows, list) or not rows:
        return jsonify({"success": False, "error": "rows must be a non-empty list"}), 400
    if len(rows) > 5000:
        return jsonify({"success": False, "error": "Too many rows in one import (max 5000)"}), 400
    try:
        result = service.confirm(get_db(), int(get_jwt_identity()), rows)
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    return jsonify({"success": True, **result})


@statement_import_bp.route("/transactions", methods=["GET"])
@jwt_required()
def list_transactions():
    month = request.args.get("month")
    rows = service.list_transactions(get_db(), int(get_jwt_identity()), month,
                                     request.args.get("limit", 500, type=int))
    return jsonify({"success": True, "transactions": rows, "count": len(rows)})


@statement_import_bp.route("/recurring", methods=["GET"])
@jwt_required()
def recurring():
    return jsonify({"success": True, **service.recurring_summary(get_db(), int(get_jwt_identity()))})


@statement_import_bp.route("/batch/<batch_id>", methods=["DELETE"])
@jwt_required()
def undo_import(batch_id):
    result = service.undo_batch(get_db(), int(get_jwt_identity()), batch_id)
    if result["transactions_removed"] == 0:
        return jsonify({"success": False, "error": "Import batch not found"}), 404
    return jsonify({"success": True, **result})
