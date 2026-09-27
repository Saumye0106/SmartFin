"""
Budget domain helpers.
Shared by the budget blueprint and the legacy scorer's /api/predict/from-budget
endpoint, which derives its input features from tracked budget + expense data.
"""

from datetime import datetime

from db_core import execute_query, row_to_dict, rows_to_list

DEFAULT_EXPENSE_CATEGORIES = {
    'rent',
    'food',
    'travel',
    'shopping',
    'emi',
    'utilities',
    'healthcare',
    'education',
    'insurance',
    'other'
}


def current_month_string():
    return datetime.now().strftime('%Y-%m')


def validate_month_string(month_str):
    if not month_str:
        raise ValueError('Month is required in YYYY-MM format')
    try:
        datetime.strptime(month_str, '%Y-%m')
        return month_str
    except ValueError as exc:
        raise ValueError('Invalid month format. Use YYYY-MM') from exc


def month_date_range(month_str):
    start_dt = datetime.strptime(f'{month_str}-01', '%Y-%m-%d')
    if start_dt.month == 12:
        end_dt = datetime(start_dt.year + 1, 1, 1)
    else:
        end_dt = datetime(start_dt.year, start_dt.month + 1, 1)
    return start_dt.strftime('%Y-%m-%d'), end_dt.strftime('%Y-%m-%d')


def normalize_expense_category(category):
    if not category:
        return 'other'
    normalized = str(category).strip().lower()
    return normalized if normalized in DEFAULT_EXPENSE_CATEGORIES else 'other'


def build_budget_summary(user_id, month_str):
    month = validate_month_string(month_str)
    start_date, end_date = month_date_range(month)

    budget_row = execute_query(
        'SELECT * FROM monthly_budgets WHERE user_id = ? AND month = ?',
        (user_id, month),
        fetch_one=True
    )
    budget = row_to_dict(budget_row) if budget_row else None

    planned_rows = []
    if budget:
        planned_rows = execute_query(
            'SELECT category, planned_amount FROM budget_categories WHERE budget_id = ? ORDER BY category ASC',
            (budget['id'],),
            fetch_all=True
        ) or []

    planned_categories = {
        row['category']: float(row['planned_amount'])
        for row in planned_rows
    }

    expense_rows = execute_query(
        '''
        SELECT id, budget_id, expense_date, category, amount, note, created_at, updated_at
        FROM expense_entries
        WHERE user_id = ? AND expense_date >= ? AND expense_date < ?
        ORDER BY expense_date DESC, created_at DESC
        ''',
        (user_id, start_date, end_date),
        fetch_all=True
    ) or []

    category_actuals = {}
    total_spent = 0.0
    for row in expense_rows:
        amount = float(row['amount'])
        category = row['category']
        total_spent += amount
        category_actuals[category] = round(category_actuals.get(category, 0.0) + amount, 2)

    monthly_income = float(budget['monthly_income']) if budget else 0.0
    planned_savings = float(budget['planned_savings']) if budget else 0.0
    auto_savings = round(max(0.0, monthly_income - total_spent), 2)

    category_comparison = []
    all_categories = sorted(set(planned_categories.keys()) | set(category_actuals.keys()))
    for category in all_categories:
        planned = round(float(planned_categories.get(category, 0.0)), 2)
        actual = round(float(category_actuals.get(category, 0.0)), 2)
        variance = round(actual - planned, 2)
        category_comparison.append({
            'category': category,
            'planned': planned,
            'actual': actual,
            'variance': variance
        })

    return {
        'month': month,
        'budget': budget,
        'monthly_income': round(monthly_income, 2),
        'planned_savings': round(planned_savings, 2),
        'total_spent': round(total_spent, 2),
        'remaining_income': round(monthly_income - total_spent, 2),
        'auto_calculated_savings': auto_savings,
        'expense_count': len(expense_rows),
        'planned_categories': planned_categories,
        'category_actuals': category_actuals,
        'category_comparison': category_comparison,
        'expenses': rows_to_list(expense_rows)
    }


def build_analysis_payload_from_summary(summary):
    actuals = summary.get('category_actuals', {})
    income = float(summary.get('monthly_income', 0))
    total_spent = float(summary.get('total_spent', 0))

    return {
        'income': round(income, 2),
        'rent': round(float(actuals.get('rent', 0)), 2),
        'food': round(float(actuals.get('food', 0)), 2),
        'travel': round(float(actuals.get('travel', 0)), 2),
        'shopping': round(float(actuals.get('shopping', 0)), 2),
        'emi': round(float(actuals.get('emi', 0)), 2),
        'expenses': round(total_spent, 2),
        'savings': round(max(0.0, income - total_spent), 2)
    }
