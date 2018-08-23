import functools
import logging

from types import FunctionType

from prometheus_client import Histogram

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
