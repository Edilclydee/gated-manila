from flask import Blueprint, current_app, jsonify, render_template

from app.constants import CITIES, GATING_COLORS, GATING_LABELS
from app.models import Community

bp = Blueprint("public", __name__)


@bp.route("/")
def index():
    lat, lng = current_app.config["MAP_CENTER"]
    map_config = {
        "lat": lat,
        "lng": lng,
        "zoom": current_app.config["MAP_ZOOM"],
        "colors": GATING_COLORS,
        "labels": GATING_LABELS,
    }
    return render_template(
        "index.html",
        map_config=map_config,
        cities=CITIES,
        gating_labels=GATING_LABELS,
        gating_colors=GATING_COLORS,
    )


@bp.route("/api/communities")
def api_communities():
    """All approved communities as a GeoJSON FeatureCollection."""
    features = [c.to_feature() for c in Community.approved().order_by(Community.name).all()]
    return jsonify({"type": "FeatureCollection", "features": features})


@bp.route("/health")
def health():
    return {"status": "ok"}
