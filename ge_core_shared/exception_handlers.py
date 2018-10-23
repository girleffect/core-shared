import logging
import json

from psycopg2 import errorcodes

from project.app import DB as db

logger = logging.getLogger(__name__)

PG_ERROR_STATUS_CODE_MAP = {
    # Entire postgres error class to set the status for
    "pgclass_23": 400,

    # Specific errors to set the status for
    "UNIQUE_VIOLATION": 409,
}

def db_exceptions(exception):
    logger.error(exception)
    db.session.rollback()
    try:
        error_code = errorcodes.lookup(exception.orig.pgcode)
    except KeyError:
        return json.dumps(
            {
                "error": exception.orig.__repr__().replace("\n", " ")
            }
        ), 500

    # Postgres errors are split into different classes, the class is obtained
    # from the first 2 characters in the postgres error code. This is useful if
    # there is a need to set a status code for an entire class rather than
    # specific errors. Classes can be found here:
    # https://www.postgresql.org/docs/current/static/errcodes-appendix.html#ERRCODES-TABLE
    error_class = f"pgclass_{exception.orig.pgcode[:2]}"

    # Set the status code, check entire class first then see if specific error
    # has a status code mapped.
    http_status_code = PG_ERROR_STATUS_CODE_MAP.get(
        error_class, 500
    )
    http_status_code = PG_ERROR_STATUS_CODE_MAP.get(
        error_code, http_status_code
    )
    return json.dumps(
        {
            "error": exception.orig.pgerror.strip().replace("\n", " ")
        }
    ), http_status_code
