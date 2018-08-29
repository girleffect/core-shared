import logging
import json

from psycopg2 import errorcodes

from project.app import DB as db

logger = logging.getLogger(__name__)

PG_ERROR_STATUS_CODE_MAP = {
    "UNIQUE_VIOLATION": 409
}

def db_exceptions(exception):
    logger.error(exception)
    db.session.rollback()
    error_code = errorcodes.lookup(exception.orig.pgcode)
    return json.dumps(
        {
            "error": exception.orig.pgerror.strip().replace("\n", " ")
        }
    ), PG_ERROR_STATUS_CODE_MAP.get(error_code, 500)
