from datetime import date
from functools import wraps

from flask import Blueprint, request
from flask_login import current_user, login_required

from catchup import (
    annotate_running_balance,
    build_chart_data,
    get_balance,
    get_totals,
    run_catchup,
)
from models import Transaction, User, WithdrawalRequest, db, utcnow
from validation import parse_amount

admin_bp = Blueprint("admin", __name__)


def admin_required(f):
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if not current_user.is_admin:
            return {"error": "Forbidden"}, 403
        return f(*args, **kwargs)

    return decorated


@admin_bp.route("/api/admin/users")
@admin_required
def list_users():
    children = db.session.execute(
        db.select(User).filter_by(is_admin=False)
    ).scalars().all()
    result = []
    for child in children:
        run_catchup(child)
        result.append({**child.to_dict(), "balance": get_balance(child)})
    return result


@admin_bp.route("/api/admin/users", methods=["POST"])
@admin_required
def create_user():
    data = request.get_json()
    if not data:
        return {"error": "Request body required"}, 400

    for field in ("username", "password", "display_name"):
        if not data.get(field):
            return {"error": f"{field} is required"}, 400

    if db.session.execute(
        db.select(User).filter_by(username=data["username"])
    ).scalars().first():
        return {"error": "Username already exists"}, 409

    user = User(
        username=data["username"],
        display_name=data["display_name"],
        is_admin=False,
        monthly_allowance=float(data.get("monthly_allowance", 0)),
        starting_balance=float(data.get("starting_balance", 0)),
        allowance_start_date=date.fromisoformat(data["allowance_start_date"]) if data.get("allowance_start_date") else None,
    )
    user.set_password(data["password"])
    db.session.add(user)
    db.session.commit()

    return user.to_dict(), 201


@admin_bp.route("/api/admin/users/<int:user_id>", methods=["PUT"])
@admin_required
def update_user(user_id):
    user = db.session.get(User, user_id)
    if not user or user.is_admin:
        return {"error": "User not found"}, 404

    data = request.get_json()
    if not data:
        return {"error": "Request body required"}, 400

    if "display_name" in data:
        user.display_name = data["display_name"]
    if "monthly_allowance" in data:
        user.monthly_allowance = float(data["monthly_allowance"])
    if "starting_balance" in data:
        user.starting_balance = float(data["starting_balance"])
    if "allowance_start_date" in data:
        user.allowance_start_date = date.fromisoformat(data["allowance_start_date"]) if data["allowance_start_date"] else None
    if data.get("password"):
        user.set_password(data["password"])

    db.session.commit()
    return user.to_dict()


@admin_bp.route("/api/admin/users/<int:user_id>")
@admin_required
def user_detail(user_id):
    user = db.session.get(User, user_id)
    if not user or user.is_admin:
        return {"error": "User not found"}, 404

    run_catchup(user)
    return {
        **user.to_dict(),
        "balance": get_balance(user),
        "totals": get_totals(user),
        "chart_data": build_chart_data(user),
    }


@admin_bp.route("/api/admin/users/<int:user_id>/transactions")
@admin_required
def user_transactions(user_id):
    user = db.session.get(User, user_id)
    if not user or user.is_admin:
        return {"error": "User not found"}, 404

    run_catchup(user)

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    txn_type = request.args.get("type", None)

    stmt = db.select(Transaction).filter_by(user_id=user.id)
    if txn_type:
        stmt = stmt.filter_by(type=txn_type)

    stmt = stmt.order_by(Transaction.created_at.desc())
    pagination = db.paginate(stmt, page=page, per_page=per_page, error_out=False)

    items = list(reversed(pagination.items))
    annotated = annotate_running_balance(user, items)
    annotated.reverse()

    return {
        "transactions": annotated,
        "total": pagination.total,
        "page": pagination.page,
        "pages": pagination.pages,
    }


@admin_bp.route("/api/admin/requests")
@admin_required
def list_requests():
    status_filter = request.args.get("status", "pending")
    stmt = db.select(WithdrawalRequest)
    if status_filter != "all":
        stmt = stmt.filter_by(status=status_filter)
    requests_list = db.session.execute(
        stmt.order_by(WithdrawalRequest.created_at.desc())
    ).scalars().all()

    result = []
    for wr in requests_list:
        child = db.session.get(User, wr.user_id)
        result.append(
            {**wr.to_dict(), "child_name": child.display_name if child else "Unknown"}
        )
    return result


@admin_bp.route("/api/admin/requests/<int:request_id>", methods=["PUT"])
@admin_required
def resolve_request(request_id):
    wr = db.session.get(WithdrawalRequest, request_id)
    if not wr:
        return {"error": "Request not found"}, 404
    if wr.status != "pending":
        return {"error": "Request already resolved"}, 400

    data = request.get_json()
    if not data or data.get("status") not in ("approved", "denied"):
        return {"error": "status must be 'approved' or 'denied'"}, 400

    if data["status"] == "approved":
        amount = parse_amount(data.get("amount", wr.amount))
        if amount is None:
            return {"error": "Invalid amount"}, 400
        if amount <= 0:
            return {"error": "Amount must be positive"}, 400

    wr.status = data["status"]
    wr.resolved_at = utcnow()
    wr.resolved_by = current_user.id

    if data["status"] == "approved":
        wr.amount = amount
        txn = Transaction(
            user_id=wr.user_id,
            type="withdrawal",
            amount=wr.amount,
            description=f"Withdrawal: {wr.reason}" if wr.reason else "Withdrawal",
        )
        db.session.add(txn)

    db.session.commit()
    return wr.to_dict()


@admin_bp.route("/api/admin/users/<int:user_id>/adjust", methods=["POST"])
@admin_required
def adjust_balance(user_id):
    user = db.session.get(User, user_id)
    if not user or user.is_admin:
        return {"error": "User not found"}, 404

    data = request.get_json()
    if not data or "amount" not in data:
        return {"error": "Amount is required"}, 400

    amount = parse_amount(data["amount"])
    if amount is None:
        return {"error": "Invalid amount"}, 400

    if amount == 0:
        return {"error": "Amount cannot be zero"}, 400

    description = data.get("description", "Manual adjustment")

    txn = Transaction(
        user_id=user.id,
        type="adjustment",
        amount=amount,
        description=description,
    )
    db.session.add(txn)
    db.session.commit()

    return {"balance": get_balance(user)}, 200
