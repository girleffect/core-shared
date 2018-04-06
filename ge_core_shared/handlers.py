import json

def add_total_count(response):
    """
    Adds X-Total-Count header to list responses.

    This method expects a list in the response json. This list is specially
    crafted in db_actions. First object needs to be a dict with the key
    x_total_count and the second needs to be a list, which is the traditional
    response expected from the api.
    """
    if isinstance(response.json, list):
        if "x_total_count" in response.json[0] and isinstance(
                response.json, list):
            # Grab the expected response data.
            data = response.json.pop(1)

            # Add header with corect value.
            response.headers["X-Total-Count"] = response.json.pop(0)[
                "x_total_count"]

            # Update response data to contain the correct data structure
            response.json = data
            response.data = json.dumps(data)
    return response
