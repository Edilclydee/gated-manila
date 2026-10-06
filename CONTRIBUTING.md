# Contributing

Thanks for helping! There are two ways to contribute.

## Add or correct data
Use the website: "+ Add a community" or "Suggest an edit" on any community. An admin reviews every submission.
- Draw shapes yourself or from open sources (OpenStreetMap). Do not copy from Google Maps or other sources that forbid it.
- Give a source or evidence (a photo link, an OSM link, or "I live here").
- Never include gate codes, guard details, schedules, or residents' personal information.

## Improve the code
1. Fork the repo and create a branch.
2. Set up locally (see README) and run `python -m pytest` before and after your change.
3. Keep changes small and add tests for new behaviour, especially around submissions, approvals and security.
4. Open a pull request describing what and why.

Ground rules:
- The public map must only ever show records with `status="approved"`.
- Never store secrets in the repo; use environment variables and keep `.env.example` updated.
- Keep it beginner-friendly: simple code over clever code.

Ideas welcome: Tagalog UI, PostGIS, contributor accounts, point-in-polygon city detection for imports, version history.
