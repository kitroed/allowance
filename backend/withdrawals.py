from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from models import WithdrawalRequest, db
from notifications import notify_parent

withdrawals_bp = Blueprint("withdrawals", __name__)


@withdrawals_bp.route("/api/withdrawals", methods=["POST"])
@login_required
def create_withdrawal():
    data = request.get_json()
    if not data or not data.get("amount"):
        return jsonify({"error": "Amount is required"}), 400

    amount = float(data["amount"])
    if amount <= 0:
        return jsonify({"error": "Amount must be positive"}), 400

    wr = WithdrawalRequest(
        user_id=current_user.id,
        amount=round(amount, 2),
        reason=data.get("reason", ""),
    )
    db.session.add(wr)
    db.session.commit()

    notify_parent(
        "Withdrawal Request",
        f"{current_user.display_name} requested ${wr.amount:.2f}: {wr.reason}",
    )

    return jsonify(wr.to_dict()), 201


@withdrawals_bp.route("/api/withdrawals")
@login_required
def list_withdrawals():
    requests_list = (
        WithdrawalRequest.query.filter_by(user_id=current_user.id)
        .order_by(WithdrawalRequest.created_at.desc())
        .all()
    )
    return jsonify([r.to_dict() for r in requests_list])
