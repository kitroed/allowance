from flask import Blueprint
from flask_login import current_user, login_required

from catchup import annotate_running_balance, build_chart_data, get_balance, run_catchup
from models import Transaction, db

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/api/dashboard")
@login_required
def dashboard():
    run_catchup(current_user)

    balance = get_balance(current_user)

    recent = db.session.execute(
        db.select(Transaction)
        .filter_by(user_id=current_user.id)
        .order_by(Transaction.created_at.desc(), Transaction.id.desc())
        .limit(10)
    ).scalars().all()

    return {
        "balance": balance,
        "recent_transactions": annotate_running_balance(current_user, recent),
        "chart_data": build_chart_data(current_user),
    }
