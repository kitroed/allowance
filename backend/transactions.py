from flask import Blueprint, request
from flask_login import current_user, login_required

from catchup import annotate_running_balance, run_catchup
from models import Transaction, db

transactions_bp = Blueprint("transactions", __name__)


@transactions_bp.route("/api/transactions")
@login_required
def list_transactions():
    run_catchup(current_user)

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    txn_type = request.args.get("type", None)

    stmt = db.select(Transaction).filter_by(user_id=current_user.id)
    if txn_type:
        stmt = stmt.filter_by(type=txn_type)

    stmt = stmt.order_by(Transaction.created_at.desc(), Transaction.id.desc())
    pagination = db.paginate(stmt, page=page, per_page=per_page, error_out=False)

    return {
        "transactions": annotate_running_balance(current_user, pagination.items),
        "total": pagination.total,
        "page": pagination.page,
        "pages": pagination.pages,
    }
