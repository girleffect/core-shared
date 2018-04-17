import logging
import json

from project.app import DB as db

logger = logging.getLogger(__name__)


def db_exceptions(exception):
    logger.error(exception)
    db.session.rollback()
    return json.dumps({"error": exception._message().replace("\n", " ")}), 500
