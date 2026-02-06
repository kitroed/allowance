import os

from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_login import LoginManager

from config import Config
from models import User, db


def create_app():
    app = Flask(__name__, static_folder=None)
    app.config.from_object(Config)

    db.init_app(app)
    CORS(app, supports_credentials=True)

    login_manager = LoginManager()
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    @login_manager.unauthorized_handler
    def unauthorized():
        return {"error": "Not authenticated"}, 401

    # Register blueprints
    from admin import admin_bp
    from auth import auth_bp
    from dashboard import dashboard_bp
    from transactions import transactions_bp
    from withdrawals import withdrawals_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(transactions_bp)
    app.register_blueprint(withdrawals_bp)
    app.register_blueprint(admin_bp)

    # Seed CLI command
    from seed import seed_command

    app.cli.add_command(seed_command)

    # Serve SvelteKit static build
    static_dir = os.path.abspath(app.config["STATIC_FOLDER"])

    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_frontend(path):
        full_path = os.path.join(static_dir, path)
        if path and os.path.isfile(full_path):
            return send_from_directory(static_dir, path)
        fallback = os.path.join(static_dir, "200.html")
        if os.path.isfile(fallback):
            return send_from_directory(static_dir, "200.html")
        return "Frontend not built yet. Run 'npm run build' in the frontend directory.", 404

    with app.app_context():
        db.create_all()

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)
