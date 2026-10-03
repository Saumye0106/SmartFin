"""
Credit Report Import Blueprint (/api/import/credit-report)

preview: upload a bureau report -> accounts with payment history, nothing saved.
confirm: the reviewed accounts -> loans, payments, history and card details.
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from credit_report import service
from db_core import get_db
from statement_import.parser import StatementParseError, StatementPasswordRequired

credit_report_bp = Blueprint("credit_report", __name__, url_prefix="/api/import/credit-report")

MAX_FILE_BYTES = 15 * 1024 * 1024


@credit_report_bp.route("/preview", methods=["POST"])
@jwt_required()
def preview_report():
    upload = request.files.get("file")
    if upload is None or not upload.filename:
        return jsonify({"success": False, "error": "Choose a credit report PDF to upload"}), 400
    data = upload.read(MAX_FILE_BYTES + 1)
    if len(data) > MAX_FILE_BYTES:
        return jsonify({"success": False, "error": "File is larger than 15 MB"}), 400
    try:
        result = service.preview(get_db(), int(get_jwt_identity()), upload.filename, data,
                                 request.form.get("password") or None)
    except StatementPasswordRequired as e:
        return jsonify({"success": False, "error": str(e), "password_required": True}), 422
    except StatementParseError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    return jsonify({"success": True, **result})


@credit_report_bp.route("/confirm", methods=["POST"])
@jwt_required()
def confirm_report():
    payload = request.get_json(silent=True) or {}
    try:
        result = service.confirm(get_db(), int(get_jwt_identity()), payload.get("rows"),
                                 payload.get("bureau"), payload.get("score"))
    except ValueError as e:
        get_db().rollback()
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception:
        get_db().rollback()
        raise
    return jsonify({"success": True, **result})


@credit_report_bp.route("", methods=["GET"])
@jwt_required()
def list_reports():
    return jsonify({"success": True, **service.list_imports(get_db(), int(get_jwt_identity()))})


@credit_report_bp.route("/<batch_id>", methods=["DELETE"])
@jwt_required()
def undo_report(batch_id):
    result = service.undo_batch(get_db(), int(get_jwt_identity()), batch_id)
    if not result.pop("found"):
        return jsonify({"success": False, "error": "Import not found"}), 404
    return jsonify({"success": True, **result})
