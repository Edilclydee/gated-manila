from flask import Blueprint, current_app, render_template

bp = Blueprint("public", __name__)


@bp.route("/")
def index():
    lat, lng = current_app.config["MAP_CENTER"]
    return render_template(
        "index.html",
        center_lat=lat,
        center_lng=lng,
        zoom=current_app.config["MAP_ZOOM"],
    )


@bp.route("/health")
def health():
    return {"status": "ok"}
