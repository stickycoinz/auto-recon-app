"""Vehicle management blueprint."""
from flask import Blueprint

bp = Blueprint('vehicle', __name__, url_prefix='/vehicle')

from auto_recon_app.vehicle import routes  # noqa 