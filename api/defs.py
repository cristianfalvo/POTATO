from flask import Blueprint

api_blueprint = Blueprint("api", "api_blueprint", url_prefix="/api")
render_blueprint = Blueprint("render", "render_blueprint")
