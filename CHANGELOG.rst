Changelog
=========

next
----
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

