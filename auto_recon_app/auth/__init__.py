"""Authentication blueprint."""
from flask import Blueprint

bp = Blueprint('auth', __name__, url_prefix='/auth')

from auto_recon_app.auth import routes  # noqa 