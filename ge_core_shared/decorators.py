import functools
import logging

from types import FunctionType, ModuleType

from prometheus_client import Histogram

logger = logging.getLogger(__name__)

def _prometheus_module_metric_decorator(f: FunctionType, H: Histogram):
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
        with H.labels(call=call_key).time():
            return f(*args, **kwargs)
    return wrapper


def add_prometheus_metrics_for_module(module_: ModuleType, service_name: str):
    """
    Convenience function applying the Prometheus metrics decorator to the
    specified module's functions.
    :param module_: The module to which the instrumentation will be applied
    :param service_name: The name of the core service.
    """
    H = Histogram(f"{service_name}_call_duration_seconds", "API call duration (s)",
              ["call"])
    decorate_all_in_module(module_, _prometheus_module_metric_decorator, [], H)

def decorate_all_in_module(module_: ModuleType, decorator: FunctionType, whitelist: list, H: Histogram):
    """
    Decorate all functions in a module with the specified decorator
    :param module_: The module to interrogate
    :param decorator: The decorator to apply
    :param whitelist: Functions not to be decorated.
    :param H: The Prometheus Histogram object.
    """
    for name in dir(module_):
        if name not in whitelist:
            obj = getattr(module_, name)
            if isinstance(obj, FunctionType):
                # We only check functions that are defined in the module we
                # specified. Some of the functions in the module may have been
                # imported from other modules. These are ignored.
                if obj.__module__ == module_.__name__:
                    logger.debug(f"Adding metrics to {module_}:{name}")
                    setattr(module_, name, decorator(obj, H))
                else:
                    logger.debug(f"No metrics on {module_}:{name} because it belongs to another "
                                 f"module")
            else:
                logger.debug(f"No metrics on {module_}:{name} because it is not a coroutine or "
                             f"function")

def list_response(func):
    """
    Manipulates list data into a connexion valid tuple, required to add headers
    to responses.

    data = func(*args, **kwargs) = ([<ApiModelInstance>, ...], {"X-Total-Count": <count>})

    return [<ApiModelInstance>, ...], <http_status_code>, <headers_dict>
    """
    def wrapper(*args, **kwargs):
        list_data = func(*args, **kwargs)
        return list_data[0], 200, list_data[1]
    return wrapper
