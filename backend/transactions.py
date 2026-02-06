from flask import Blueprint, request
from flask_login import current_user, login_required

from catchup import annotate_running_balance, run_catchup
from models import Transaction

transactions_bp = Blueprint("transactions", __name__)


@transactions_bp.route("/api/transactions")
@login_required
def list_transactions():
    run_catchup(current_user)

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    txn_type = request.args.get("type", None)

    query = Transaction.query.filter_by(user_id=current_user.id)
    if txn_type:
        query = query.filter_by(type=txn_type)

    query = query.order_by(Transaction.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    # Annotate with running balance (items are desc, reverse to asc, annotate, reverse back)
    items = list(reversed(pagination.items))
    annotated = annotate_running_balance(current_user, items)
    annotated.reverse()

    return {
        "transactions": annotated,
        "total": pagination.total,
        "page": pagination.page,
        "pages": pagination.pages,
    }
