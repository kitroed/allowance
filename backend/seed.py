import click
from flask.cli import with_appcontext

from models import User, db


@click.command("seed")
@click.option("--admin-username", default="parent", help="Admin username")
@click.option(
    "--admin-password",
    default=None,
    help="Admin password (prompted if not provided)",
)
def seed_command(admin_username, admin_password):
    """Create the admin account if it doesn't exist."""
    existing = User.query.filter_by(username=admin_username).first()
    if existing:
        click.echo(f"User '{admin_username}' already exists. Skipping.")
        return

    if not admin_password:
        admin_password = click.prompt("Admin password", hide_input=True)

    admin = User(
        username=admin_username,
        display_name="Parent",
        is_admin=True,
        monthly_allowance=0,
    )
    admin.set_password(admin_password)
    db.session.add(admin)
    db.session.commit()
    click.echo(f"Admin user '{admin_username}' created.")
