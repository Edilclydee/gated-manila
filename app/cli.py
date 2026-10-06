import click
from flask.cli import with_appcontext

from app import db
from app.models import Admin
from app.sample_data import clear_samples, seed_samples


@click.command("init-db")
@with_appcontext
def init_db_command():
    """Create all database tables."""
    from app.schema import ensure_schema

    changes = ensure_schema()
    click.echo("Database initialised." + (f" Updated: {', '.join(changes)}." if changes else ""))


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


@click.command("import-osm")
@click.option("--dry-run", is_flag=True, help="Show what would be imported without saving anything.")
@click.option("--broad", is_flag=True, help="Also include residential areas whose names look like subdivisions.")
@click.option("--limit", type=int, default=None, help="Import at most this many records.")
@click.option("--file", "file_path", type=click.Path(exists=True, dir_okay=False),
              help="Read a saved Overpass JSON file instead of downloading.")
@click.option("--save", "save_path", type=click.Path(dir_okay=False),
              help="Save the downloaded Overpass response to this file.")
@with_appcontext
def import_osm_command(dry_run, broad, limit, file_path, save_path):
    """Add OpenStreetMap candidates to the pending review queue."""
    import json

    from app.osm_import import OsmImportError, fetch_overpass, load_elements, run_import

    try:
        if file_path:
            elements = load_elements(file_path)
        else:
            click.echo("Downloading from Overpass (this can take a few minutes)...")
            elements, failed = fetch_overpass(broad=broad, progress=click.echo)
            if failed:
                click.echo(f"WARNING: {len(failed)} small area(s) could not be downloaded; "
                           "re-run later to fill the gaps (items already imported are skipped).")
                if not elements:
                    raise click.ClickException("Nothing could be downloaded. Try again later.")
            if save_path:
                with open(save_path, "w", encoding="utf-8") as fh:
                    json.dump({"elements": elements}, fh)
                click.echo(f"Saved raw response to {save_path}")
    except OsmImportError as err:
        raise click.ClickException(str(err))

    stats = run_import(elements, dry_run=dry_run, limit=limit)
    verb = "Would create" if dry_run else "Created"
    click.echo(f"Found {stats['found']} elements.")
    click.echo(f"{verb} {stats['created']} pending submissions.")
    click.echo(f"Already imported or submitted: {stats['duplicates']}.")
    for reason, count in sorted(stats["skipped"].items()):
        click.echo(f"Skipped {count}: {reason}.")
