import logging
import json

from project.settings import SQLALCHEMY_DB as db

logger = logging.getLogger(__name__)


def db_exceptions(exception):
    logger.error(exception)
    db.session.rollback()
    return json.dumps({"error": exception._message().replace("\n", " ")}), 500
