from datetime import datetime, timedelta

from flask import Blueprint, jsonify
from flask_login import current_user, login_required

from catchup import annotate_running_balance, get_balance, run_catchup
from models import Transaction

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/api/dashboard")
@login_required
def dashboard():
    run_catchup(current_user)

    balance = get_balance(current_user)

    recent = (
        Transaction.query.filter_by(user_id=current_user.id)
        .order_by(Transaction.created_at.desc())
        .limit(10)
        .all()
    )

    # Chart data: daily balance for the last 90 days
    ninety_days_ago = datetime.utcnow() - timedelta(days=90)
    all_txns = (
        Transaction.query.filter_by(user_id=current_user.id)
        .order_by(Transaction.created_at.asc())
        .all()
    )

    # Build running balance series
    labels = []
    balances = []
    running = 0.0
    for txn in all_txns:
        if txn.type in ("income", "interest", "adjustment"):
            running += txn.amount
        else:
            running -= txn.amount

        if txn.created_at >= ninety_days_ago:
            day_label = txn.created_at.strftime("%Y-%m-%d")
            # Collapse multiple transactions on the same day to the last one
            if labels and labels[-1] == day_label:
                balances[-1] = round(running, 2)
            else:
                labels.append(day_label)
                balances.append(round(running, 2))

    return jsonify(
        {
            "balance": balance,
            "recent_transactions": annotate_running_balance(
                current_user, list(reversed(recent))
            )[::-1],
            "chart_data": {"labels": labels, "balances": balances},
        }
    )
