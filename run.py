from app import create_app
from app.schema import ensure_schema

app = create_app()

if __name__ == "__main__":
    # Creates missing tables and applies small upgrades (safe to repeat) before starting.
    with app.app_context():
        ensure_schema()
    app.run(debug=True)
