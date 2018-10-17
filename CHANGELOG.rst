Changelog
=========

next
----
#. Change authentication middleware, to no longer be object based.
#. Collapse all 404 and 401 paths in the metric middleware.

1.2.0
-----
The `get_or_create()` function now takes an extra `defaults` argument which is used to provide values for fields that needs to be populated on
creation, but not used for lookups.

1.1.3
-----
Added db exception decorator to be used for flask SQLAlchemy based tests on services.

1.1.2
-----
Update to db exception handler, allows for status code mapping to database errors.

1.1.1
-----
Added Metrics Middleware and Decorator for synchronous flask services.

1.1.0
-----
Added support for unprotected API end-points.

1.0.1
-----
Fixed bug in Transformation constructor, which used a mutable default function parameter.

0.1.2
-----
#. Refactor list action return value, from list to tuple. Tuple contains list of objects and dictionary containing total count.
#. Added decorator to alter list controller return values to be connexion valid response tuple.

0.1.1
-----
#. transformations.py added.
#. exception_handlers.py added.
#. middleware.py added.

0.1.0
-----
#. DB actions added, makes use of generic project settings imports.

