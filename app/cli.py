import click
from flask.cli import with_appcontext

from app import db
from app.models import Admin
from app.sample_data import clear_samples, seed_samples


@click.command("init-db")
@with_appcontext
def init_db_command():
    """Create all database tables."""
    db.create_all()
    click.echo("Database initialised.")


@click.command("create-admin")
@click.argument("username")
@click.password_option()
@with_appcontext
def create_admin_command(username, password):
    """Create an admin account: python -m flask --app run create-admin USERNAME"""
    if Admin.query.filter_by(username=username).first():
        raise click.ClickException(f"Admin '{username}' already exists.")
    admin = Admin(username=username)
    try:
        admin.set_password(password)
    except ValueError as err:
        raise click.ClickException(str(err))
    db.session.add(admin)
    db.session.commit()
    click.echo(f"Admin '{username}' created.")


@click.command("seed-sample")
@with_appcontext
def seed_sample_command():
    """Add fake SAMPLE communities for local testing."""
    click.echo(f"Added {seed_samples()} sample communities.")


@click.command("clear-sample")
@with_appcontext
def clear_sample_command():
    """Remove all SAMPLE communities."""
    click.echo(f"Removed {clear_samples()} sample communities.")
