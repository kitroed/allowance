from flask import Blueprint, request
from flask_login import current_user, login_required, login_user, logout_user

from models import User, db

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data or not data.get("username") or not data.get("password"):
        return {"error": "Username and password required"}, 400

    user = db.session.execute(db.select(User).filter_by(username=data["username"])).scalars().first()
    if not user or not user.check_password(data["password"]):
        return {"error": "Invalid username or password"}, 401

    login_user(user, remember=True)
    return {"ok": True, "user": user.to_dict()}


@auth_bp.route("/api/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return {"ok": True}


@auth_bp.route("/api/me")
@login_required
def me():
    return {"user": current_user.to_dict()}
