"""
Budget Blueprint
Monthly budget CRUD, expense entry CRUD, and derived summary/analysis endpoints.
"""

import uuid
from datetime import datetime

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from db_core import execute_query, row_to_dict, rows_to_list
from budget.service import (
    current_month_string,
    validate_month_string,
    month_date_range,
    normalize_expense_category,
    build_budget_summary,
    build_analysis_payload_from_summary,
)

budget_bp = Blueprint('budget', __name__)


@budget_bp.route('/api/budget/monthly', methods=['POST'])
@jwt_required()
def upsert_monthly_budget():
    """
    Create or update the authenticated user's monthly budget.
    Body: month (YYYY-MM), monthly_income, planned_savings (optional), category_budgets (optional dict)
    """
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json() or {}

        month = validate_month_string(data.get('month', current_month_string()))
        monthly_income = float(data.get('monthly_income', 0))
        planned_savings = float(data.get('planned_savings', 0))

        if monthly_income < 0 or planned_savings < 0:
            return jsonify({'error': 'monthly_income and planned_savings must be non-negative'}), 400

        existing = execute_query(
            'SELECT id FROM monthly_budgets WHERE user_id = ? AND month = ?',
            (user_id, month),
            fetch_one=True
        )

        now_iso = datetime.now().isoformat()
        budget_id = existing['id'] if existing else str(uuid.uuid4())

        if existing:
            execute_query(
                '''
                UPDATE monthly_budgets
                SET monthly_income = ?, planned_savings = ?, updated_at = ?
                WHERE id = ?
                ''',
                (monthly_income, planned_savings, now_iso, budget_id),
                commit=True
            )
        else:
            execute_query(
                '''
                INSERT INTO monthly_budgets (id, user_id, month, monthly_income, planned_savings, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ''',
                (budget_id, user_id, month, monthly_income, planned_savings, now_iso, now_iso),
                commit=True
            )

        category_budgets = data.get('category_budgets', {})
        if isinstance(category_budgets, dict):
            execute_query(
                'DELETE FROM budget_categories WHERE budget_id = ?',
                (budget_id,),
                commit=True
            )
            for raw_category, raw_amount in category_budgets.items():
                category = normalize_expense_category(raw_category)
                amount = float(raw_amount or 0)
                if amount < 0:
                    return jsonify({'error': f'Category budget for {category} cannot be negative'}), 400
                execute_query(
                    '''
                    INSERT INTO budget_categories (id, budget_id, category, planned_amount, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ''',
                    (str(uuid.uuid4()), budget_id, category, amount, now_iso, now_iso),
                    commit=True
                )

        summary = build_budget_summary(user_id, month)
        return jsonify({'success': True, 'summary': summary}), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@budget_bp.route('/api/budget/monthly', methods=['GET'])
@jwt_required()
def get_monthly_budget():
    """Get budget summary for a month (defaults to current month)."""
    try:
        user_id = int(get_jwt_identity())
        month = request.args.get('month', current_month_string())
        summary = build_budget_summary(user_id, month)
        return jsonify({'success': True, 'summary': summary}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@budget_bp.route('/api/budget/expenses', methods=['POST'])
@jwt_required()
def create_expense_entry():
    """
    Add an expense entry for the authenticated user.
    Body: amount, category, expense_date (YYYY-MM-DD optional), note (optional)
    """
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json() or {}

        amount = float(data.get('amount', 0))
        if amount <= 0:
            return jsonify({'error': 'amount must be greater than 0'}), 400

        category = normalize_expense_category(data.get('category'))
        note = data.get('note', '')

        raw_date = data.get('expense_date', datetime.now().strftime('%Y-%m-%d'))
        try:
            expense_dt = datetime.strptime(raw_date, '%Y-%m-%d')
        except ValueError:
            return jsonify({'error': 'expense_date must be in YYYY-MM-DD format'}), 400

        month = expense_dt.strftime('%Y-%m')
        budget_row = execute_query(
            'SELECT id FROM monthly_budgets WHERE user_id = ? AND month = ?',
            (user_id, month),
            fetch_one=True
        )
        budget_id = budget_row['id'] if budget_row else None

        now_iso = datetime.now().isoformat()
        expense_id = str(uuid.uuid4())
        execute_query(
            '''
            INSERT INTO expense_entries (id, user_id, budget_id, expense_date, category, amount, note, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (expense_id, user_id, budget_id, expense_dt.strftime('%Y-%m-%d'), category, amount, note, now_iso, now_iso),
            commit=True
        )

        expense = execute_query(
            'SELECT * FROM expense_entries WHERE id = ?',
            (expense_id,),
            fetch_one=True
        )

        summary = build_budget_summary(user_id, month)
        return jsonify({'success': True, 'expense': row_to_dict(expense), 'summary': summary}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@budget_bp.route('/api/budget/expenses', methods=['GET'])
@jwt_required()
def list_expense_entries():
    """List expense entries with optional month/category filters."""
    try:
        user_id = int(get_jwt_identity())
        month = request.args.get('month')
        category = request.args.get('category')
        limit = min(max(int(request.args.get('limit', 200)), 1), 1000)

        query = '''
            SELECT * FROM expense_entries
            WHERE user_id = ?
        '''
        params = [user_id]

        if month:
            month = validate_month_string(month)
            start_date, end_date = month_date_range(month)
            query += ' AND expense_date >= ? AND expense_date < ?'
            params.extend([start_date, end_date])

        if category:
            query += ' AND category = ?'
            params.append(normalize_expense_category(category))

        query += ' ORDER BY expense_date DESC, created_at DESC LIMIT ?'
        params.append(limit)

        rows = execute_query(query, tuple(params), fetch_all=True) or []
        return jsonify({'success': True, 'expenses': rows_to_list(rows), 'count': len(rows)}), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@budget_bp.route('/api/budget/expenses/<expense_id>', methods=['PUT'])
@jwt_required()
def update_expense_entry(expense_id):
    """Update a single expense entry owned by the authenticated user."""
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json() or {}

        existing = execute_query(
            'SELECT * FROM expense_entries WHERE id = ? AND user_id = ?',
            (expense_id, user_id),
            fetch_one=True
        )
        if not existing:
            return jsonify({'error': 'Expense not found'}), 404

        updates = []
        params = []

        if 'amount' in data:
            amount = float(data['amount'])
            if amount <= 0:
                return jsonify({'error': 'amount must be greater than 0'}), 400
            updates.append('amount = ?')
            params.append(amount)

        if 'category' in data:
            updates.append('category = ?')
            params.append(normalize_expense_category(data['category']))

        if 'note' in data:
            updates.append('note = ?')
            params.append(str(data.get('note', '')))

        if 'expense_date' in data:
            try:
                expense_dt = datetime.strptime(data['expense_date'], '%Y-%m-%d')
                updates.append('expense_date = ?')
                params.append(expense_dt.strftime('%Y-%m-%d'))
            except ValueError:
                return jsonify({'error': 'expense_date must be in YYYY-MM-DD format'}), 400

        if not updates:
            return jsonify({'error': 'No valid fields provided for update'}), 400

        updates.append('updated_at = ?')
        params.append(datetime.now().isoformat())
        params.extend([expense_id, user_id])

        execute_query(
            f"UPDATE expense_entries SET {', '.join(updates)} WHERE id = ? AND user_id = ?",
            tuple(params),
            commit=True
        )

        updated = execute_query(
            'SELECT * FROM expense_entries WHERE id = ?',
            (expense_id,),
            fetch_one=True
        )

        month = datetime.strptime(updated['expense_date'], '%Y-%m-%d').strftime('%Y-%m')
        summary = build_budget_summary(user_id, month)
        return jsonify({'success': True, 'expense': row_to_dict(updated), 'summary': summary}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@budget_bp.route('/api/budget/expenses/<expense_id>', methods=['DELETE'])
@jwt_required()
def delete_expense_entry(expense_id):
    """Delete an expense entry owned by the authenticated user."""
    try:
        user_id = int(get_jwt_identity())
        existing = execute_query(
            'SELECT * FROM expense_entries WHERE id = ? AND user_id = ?',
            (expense_id, user_id),
            fetch_one=True
        )
        if not existing:
            return jsonify({'error': 'Expense not found'}), 404

        month = datetime.strptime(existing['expense_date'], '%Y-%m-%d').strftime('%Y-%m')
        execute_query(
            'DELETE FROM expense_entries WHERE id = ? AND user_id = ?',
            (expense_id, user_id),
            commit=True
        )
        summary = build_budget_summary(user_id, month)

        return jsonify({'success': True, 'message': 'Expense deleted', 'summary': summary}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@budget_bp.route('/api/budget/summary', methods=['GET'])
@jwt_required()
def get_budget_summary():
    """Get monthly budget summary (totals + category comparison + expenses)."""
    try:
        user_id = int(get_jwt_identity())
        month = request.args.get('month', current_month_string())
        summary = build_budget_summary(user_id, month)
        return jsonify({'success': True, 'summary': summary}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@budget_bp.route('/api/budget/analysis-input', methods=['GET'])
@jwt_required()
def get_budget_analysis_input():
    """Return analyzer-ready payload derived from tracked budget + expenses for a month."""
    try:
        user_id = int(get_jwt_identity())
        month = request.args.get('month', current_month_string())
        summary = build_budget_summary(user_id, month)
        analysis_input = build_analysis_payload_from_summary(summary)

        return jsonify({
            'success': True,
            'month': summary['month'],
            'analysis_input': analysis_input,
            'summary': {
                'monthly_income': summary['monthly_income'],
                'total_spent': summary['total_spent'],
                'auto_calculated_savings': summary['auto_calculated_savings'],
                'expense_count': summary['expense_count']
            }
        }), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500
