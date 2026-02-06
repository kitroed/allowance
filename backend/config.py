import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-in-production")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///allowance.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Interest rates (annualized)
    SAVINGS_INTEREST_RATE = float(os.environ.get("SAVINGS_INTEREST_RATE", "0.05"))
    CREDIT_INTEREST_RATE = float(os.environ.get("CREDIT_INTEREST_RATE", "0.24"))

    # ntfy
    NTFY_SERVER = os.environ.get("NTFY_SERVER", "")
    NTFY_TOPIC = os.environ.get("NTFY_TOPIC", "allowance")

    # Static files (frontend build output)
    STATIC_FOLDER = os.environ.get("STATIC_FOLDER", "../frontend/build")
