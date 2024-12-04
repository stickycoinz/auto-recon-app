"""Workflow management blueprint."""
from flask import Blueprint

bp = Blueprint('workflow', __name__, url_prefix='/workflow')

from auto_recon_app.workflow import routes  # noqa 