# Gated Manila

A community-sourced map of gated communities and subdivisions in Metro Manila and nearby provinces (Rizal, Cavite, Bulacan and Laguna).
Anyone can submit a community or suggest an edit. An admin reviews every submission before it appears on the public map.

**Status:** Phase 1 MVP (map, submissions, admin review, OpenStreetMap import).

## Features
- Public map (Leaflet + OpenStreetMap tiles) with searchable province and city filters, plus status and name filters
- Submission form with polygon drawing or pin drop, protected by Cloudflare Turnstile, a honeypot and rate limiting
- "Suggest an edit" on any community; edits never change live data until approved
- Admin login, review queue, edit-before-approve, reject with reason, and unpublish/republish for takedowns
- Importer that adds OpenStreetMap candidates to the review queue

## Quick start (Windows)

```
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
copy .env.example .env
python -m flask --app run init-db
python -m flask --app run create-admin yourname
python run.py
```

On macOS or Linux, use `source .venv/bin/activate` and `cp` instead. Open http://127.0.0.1:5000.
If PowerShell blocks the activate script, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once.
We use `python -m flask` and `python -m pip` because they avoid blocked `.exe` launchers on some Windows setups.

Admin pages live at `/admin/login`.

**Upgrading an older database?** Run `python -m flask --app run init-db` once. It adds the new `province` column and keeps your data (existing entries become Metro Manila). `python run.py` also does this automatically.

**Supported areas:** the provinces and their cities are listed in `PROVINCES` in `app/constants.py`; the area where shapes may be drawn is `REGION_BOUNDS` in the same file. Add a province by editing those two.

## Useful commands

| Command | What it does |
|---|---|
| `python -m flask --app run seed-sample` | Add 5 fake SAMPLE communities for testing |
| `python -m flask --app run clear-sample` | Remove the SAMPLE communities |
| `python -m flask --app run import-osm --dry-run` | Preview an OpenStreetMap import (nothing saved) |
| `python -m flask --app run import-osm --limit 20` | Import up to 20 candidates into the pending queue |
| `python -m flask --app run import-osm --broad` | Also include residential areas named like subdivisions |
| `python -m flask --app run import-osm --save osm.json` | Download and keep the raw response |
| `python -m flask --app run import-osm --file osm.json` | Import from a saved file instead of downloading |
| `python -m pytest` | Run the tests |

### About the OpenStreetMap import
Imported records are **never public automatically**. Each becomes a pending submission with a link back to its OSM element. The importer does not assume a gating status (it is left as "open or unclear") and only fills in the province and city when the OSM address tags match a supported city or municipality; otherwise the reviewer picks them. It currently downloads the Metro Manila area and its edges. Records you reject are not re-imported.
The importer uses the public Overpass API; please be gentle (use `--save` and `--file` rather than re-downloading repeatedly).

## Configuration
All settings are environment variables (see `.env.example`). Never commit `.env`.

## Project layout
```
app/            Flask app: models, routes, validation, importer, templates, static files
tests/          Automated tests
config.py       Settings
run.py          Start the dev server
```

## Privacy rule
This project records boundaries and public facts only. Do not submit gate codes, guard details, schedules, or residents' personal information.
Submitter contact details are optional, private, and only visible to admins.

## Takedowns and corrections
Anyone can use "Suggest an edit" to correct an entry. Owners of a community, homeowners' associations and LGUs who want an entry corrected or removed should contact the maintainers; admins can unpublish an entry immediately.

## Licenses
- **Code:** see `LICENSE`.
- **Data:** Open Database License (ODbL) 1.0. See `DATA_LICENSE.md`.

## Contributing
See `CONTRIBUTING.md`.
