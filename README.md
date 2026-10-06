# Gated Manila

A community-sourced map of gated communities and subdivisions in Metro Manila.
Anyone can submit a community or suggest an edit; an admin approves it before it appears on the public map.

**Status:** early development (Phase 1 MVP).

## Stack
Flask, SQLite (SQLAlchemy), Leaflet, OpenStreetMap tiles, Cloudflare Turnstile.

## Run locally

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
copy .env.example .env          # Windows
# cp .env.example .env          # macOS / Linux

# 4. Start the app
python run.py
```

Open http://127.0.0.1:5000 to see the map.

## Privacy rule
This project records boundaries and public facts only. Do not submit gate codes, guard details, or residents' personal information.

## Licenses
Code: see LICENSE. Data: ODbL (to be documented in DATA_LICENSE.md).
