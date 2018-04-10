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
