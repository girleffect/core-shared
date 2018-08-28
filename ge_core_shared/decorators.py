import functools
import inspect
import logging

from types import FunctionType, ModuleType
from typing import Type

from flask_sqlalchemy import SQLAlchemy
from prometheus_client import Histogram

DB = SQLAlchemy()

logger = logging.getLogger(__name__)

class MetricDecoration:

    __instance = None

    def __init__(self, modules, service_name, whitelist=None):
        if MetricDecoration.__instance:
            raise Exception("MetricDecoration instance exists: Singleton")
        else:
            MetricDecoration.__instance = self
            self.modules = modules
            self.H = Histogram(f"{service_name}_call_duration_seconds", "API call duration (s)",
              ["call"])
            self.whitelist = whitelist or []

    def decorate_all_in_modules(self):
        """
        Decorate all functions in a module with the specified decorator
        """
        for module_ in self.modules:
            for name in dir(module_):
                if name not in self.whitelist:
                    obj = getattr(module_, name)
                    if isinstance(obj, FunctionType):
                        # We only check functions that are defined in the module we
                        # specified. Some of the functions in the module may have been
                        # imported from other modules. These are ignored.
                        if obj.__module__ == module_.__name__:
                            logger.debug(f"Adding metrics to {module_}:{name}")
                            setattr(module_, name, self._prometheus_module_metric_decorator(obj))
                        else:
                            logger.debug(f"No metrics on {module_}:{name} because it belongs to another "
                                         f"module")
                    else:
                        logger.debug(f"No metrics on {module_}:{name} because it is not a coroutine or "
                                     f"function")


    def _prometheus_module_metric_decorator(self, f: FunctionType):
        """
        A Prometheus decorator adding timing metrics to a function.
        This decorator will work on both asynchronous and synchronous functions.
        Note, however, that this function will turn synchronous functions into
        asynchronous ones when used as a decorator.
        :param f: The function for which to capture metrics
        """
        module_ = f.__module__.split(".")[-1]
        call_key = "{}_{}".format(module_, f.__name__)
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            with self.H.labels(call=call_key).time():
                return f(*args, **kwargs)
        return wrapper


def _db_exception(func: FunctionType):
    """
    Wrap a function with a try except to rollback a DB transaction on exception and raise.
    :param f: The function to be wrapped
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            DB.session.close_all()
            raise e

    return wrapper


def decorate_tests_in_directory(directory, whitelist: list):
    """
    Go through all tests found the directory and wrap their class functions.
    :param directory: The directory to be looked in.
    :param whitelist: The test modules to be omitted from the decoration.
    """
    if getattr(directory, "__all__"):
        for test in directory.__all__:
            if test not in whitelist:
                obj = getattr(directory, test)
                if inspect.ismodule(obj) and test.__name__.startswith("test"):
                    decorate_classes_in_module(obj, _db_exception)


def decorate_classes_in_module(module_: ModuleType, decorator: FunctionType):
    """
    Go through all classes in module to decorate all class functions.
    :param module_: Module in question
    """
    for name in dir(module_):
        if inspect.isclass(name) and name.__module__ == module_.__name__:
            decorate_all_in_class(module_, decorator, [])


def decorate_all_in_class(klass: Type, decorator: FunctionType, whitelist: list):
    """
    Decorate all functions in a class with the specified decorator
    :param klass: The class to interrogate
    :param decorator: The decorator to apply
    :param whitelist: Functions not to be decorated.
    """
    for name in dir(klass):
        if name not in whitelist:
            obj = getattr(klass, name)
            if isinstance(obj, FunctionType):
                logger.debug(f"Adding metrics to {klass}:{name}")
                setattr(klass, name, decorator(obj))
            else:
                logger.debug(f"No metrics on {klass}:{name} because it is not a function")


def list_response(func):
    """
    Manipulates list data into a connexion valid tuple, required to add headers
    to responses.

    data = func(*args, **kwargs) = ([<ApiModelInstance>, ...], {"X-Total-Count": <count>})

    return [<ApiModelInstance>, ...], <http_status_code>, <headers_dict>
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        list_data = func(*args, **kwargs)
        return list_data[0], 200, list_data[1]
    return wrapper
