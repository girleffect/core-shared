"""
This module defines classes that helps to transform dictionaries.
Their purpose is to simply mapping server to client classes and vice versa.

At a high level the following happens:

```
1. body_dict = request.get_json()  # Read the request body as JSON, returning a dict
2. server_model = CreatePolicyServerModel.from_dict(body_dict)  # The server
model needs to be created, since it does the validation
3. server_model_as_dict = server_model.to_dict()
4. client_model_dict = TheTransform.apply(server_model_as_dict)
5. client_model = CreatePolicyClientModel.from_dict(client_model_dict)
```

Note: Step 5 can also be written as
```
client_model = CreatePolicyClientModel(**client_model_dict)
```
The process for the response from the client is similar. The class returned
needs to be converted to a dictionary, transformed and used to construct the
server response class.

"""
import logging

LOGGER = logging.getLogger(__name__)


class Mapping(object):
    """
    A class representing a mapping definition

    The mapping will be applied to a dictionary field
    """
    def __init__(self, input_field, output_field=None, conversion=None):
        """
        :param input_field: The name of the field to transform
        :param output_field: The name of the new field name that should be
          used. If omitted, the name of the input field is used
        :param conversion: A callable used to map the value. If None,
          the value of the input field is copied verbatim.
        """
        self.input_field = input_field
        self.output_field = output_field or input_field
        self.conversion = conversion


class Transformation(object):
    """
    A transformation is a list of Mappings that can be applied to a dictionary.
    """
    def __init__(self, mappings: [Mapping] = None,
                 copy_fields: [str] = None):
        """
        :param mappings: Mappings for fields
        :param copy_fields: Convenience mechanism for fields that should
        only be copied.
        """
        copy_fields = copy_fields or []
        self._mappings = mappings or []
        self._mappings.extend([Mapping(field) for field in copy_fields])

        # Verify that there are no duplicate input field names specified
        self._check_duplicates(
            [mapping.input_field for mapping in self._mappings]
        )
        # Verify that there are no duplicate output field names specified
        self._check_duplicates(
            [mapping.output_field for mapping in self._mappings]
        )

    def apply(self, dictionary: dict) -> dict:
        """
        Apply this transformation to the specified
        :param dictionary: The dictionary to transform
        :return: The transformed dictionary
        """
        result = {}
        for mapping in self._mappings:
            if mapping.input_field in dictionary:
                value = dictionary[mapping.input_field]
                if mapping.conversion is not None:
                    try:
                        value = mapping.conversion(value)
                    except Exception as e:
                        msg = "Field mapping failed with '{}'\n" \
                              "Field: '{}'\n" \
                              "Value: '{}'\n" \
                              "Conversion: {}".format(e, mapping.input_field,
                                                      value, mapping.conversion)
                        LOGGER.error(msg)
                        raise RuntimeError(msg)

                # If there is not value present, do not add the null value to
                # the return values. Swagger spec generated models, do not
                # expect null values and will raise errors accordingly.
                if value is None:
                    continue

                result[mapping.output_field] = value

        return result

    def _check_duplicates(self, names):
        # Verify that there are no duplicate field names specified
        seen = set()
        for name in names:
            if name in seen:
                raise RuntimeError("Field '{}' specified more than "
                                   "once".format(name))
            seen.add(name)
