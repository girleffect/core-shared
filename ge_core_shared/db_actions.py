import importlib
import typing

from sqlalchemy import func

from project import settings
from project.app import DB as db

models = importlib.import_module(settings.ACTION_MODELS)
mappings = importlib.import_module(settings.ACTION_MAPPINGS)

ApiModel = typing.TypeVar("ApiModel")
SqlAlchemyModel = typing.TypeVar("SqlAlchemyModel")


def crud(
        model: typing.Type[SqlAlchemyModel],
        api_model: typing.Type[ApiModel],
        action: str,
        data: dict = None,
        query: dict = None) -> typing.Union[ApiModel, typing.List[ApiModel], None]:
    model = getattr(models, model)
    """
    Primary purpose of this method is to cut down on code duplication within
    the controller methods.

    It attempts to find a method based on the action that got passed along.
    In the event the method does not exist, it is left to raise an error, as
    this method can not be allowed to be implemented incorrectly.

    The SQLAlchemy model and API model classes are always passed to the action
    methods. While data and query data are passed along as kwargs for all
    methods. It is up to the specific method to make use of either or both as
    needed.
    Once again methods are left to raise errors, in this case KeyErrors if the
    required key and value is not present in data or query.

    :param model: SQLAlchemy model class.
    :param api_model: Swagger API model class
    :return: Swagger API model instance
    :return: List[Swagger API model instance]
    :return: None, only delete can return this.
    """
    return transform(
        globals()["%s_entry" % action](
            model=model,
            **{"data": data, "query": query}
        ),
        api_model=api_model
    )


def create_entry(model: typing.Type[SqlAlchemyModel], **kwargs) -> SqlAlchemyModel:
    """
    Instantiate a SQLAlchemy model instance and saves it to the corresponding
    database table.
    """
    instance = model(**kwargs["data"])
    db.session.add(instance)
    db.session.commit()
    return instance


def read_entry(model: typing.Type[SqlAlchemyModel], **kwargs) -> SqlAlchemyModel:
    """
    Does a database select, based of of the query data provided, returns the
    first object in the result set.

    Raises a 404 if data can not be found.
    """
    # Get query only takes PKs, no kwargs. Filter however is more flexible.
    instance = model.query.filter_by(**kwargs["query"]).first_or_404()
    return instance


def update_entry(model: typing.Type[SqlAlchemyModel], **kwargs) -> SqlAlchemyModel:
    """
    Does a database select, based of of the query data provided, readies up an
    instance of the specific model based on the result data.
    Instance is then altered with the new data and saved to the database.

    Raises a 404 if initial data can not be found.
    """
    instance = model.query.filter_by(**kwargs["query"]).first_or_404()
    for key, value in kwargs["data"].items():
        setattr(instance, key, value)
    db.session.commit()
    return instance


def delete_entry(model: typing.Type[SqlAlchemyModel], **kwargs) -> None:
    """
    Does a database select, based of of the query data provided, readies up an
    instance of the specific model based on the result data.
    Instance is then passed as parameter for deletion.

    Raises a 404 if initial data can not be found.
    """
    instance = model.query.filter_by(**kwargs["query"]).first_or_404()
    db.session.delete(instance)
    db.session.commit()


def list_entry(model: typing.Type[SqlAlchemyModel], **kwargs) -> typing.List[SqlAlchemyModel]:
    """
    Builds a SQLAlchemy query up from incoming kwargs.

    Finally returns a list of SQLAlchemy model instances.
    """
    query = db.session.query(model, func.count().over().label("x_total_count"))
    ids = kwargs["query"].get("ids")
    if ids:
        # Need to do some more work to handle composite PKs. Pass the set of
        # ids in a dictionary.
        if isinstance(ids, dict):
            # Unpack the dictionary and only do some work if the value is not
            # None. No sense in passing another filter value if it has to do
            # nothing.
            for key, _id in ids.items():
                if _id is not None:
                    query = query.filter(
                        getattr(model, key).in_(
                            _id if isinstance(_id, list) else [_id]
                        )
                    )
        else:
            query = query.filter(model.id.in_(ids))

    # Append order by
    # NOTE: order_by(SqlAlchemyModel.column, SqlAlchemyModel.column ...) is
    # equal to order_by(SqlAlchemyModel.column).order_by(
    # SqlAlchemyModel.column)...
    for column in kwargs["query"]["order_by"]:
        query = query.order_by(getattr(model, column))

    return query.offset(
        kwargs["query"].get("offset", 0)
    ).limit(
        kwargs["query"].get("limit", settings.DEFAULT_API_LIMIT)
    ).all()


def transform(
        instance: typing.Union[SqlAlchemyModel, typing.List[SqlAlchemyModel]],
        api_model: typing.Type[ApiModel]) -> \
        typing.Union[ApiModel, typing.List[ApiModel]]:
    """
    Translates a SqlAlchemy model instance or list of SqlAlchemy model
    instances into a Swagger API model instance or list of Swagger API model
    instances, respectively. To assist with json serialization later on in
    flask.

    :param instance: SQLAlchemy model instance OR
    :param instance: List[SQLAlchemy model instances]
    :param api_model: Swagger API model class
    :return: Swagger API model instance
    :return: List[Swagger API model instances]
    """
    data = None

    # If there is nothing to return we return immediately.
    if instance is None:
        return None
    elif instance == []:
        return [], {"X-Total-Count": 0}

    is_list = isinstance(instance, list)

    # Grab model name from the SQLAlchemy model class, as this transforms from
    # DB to API.
    model_name = instance.__class__.__name__ \
        if not is_list else instance[0][0].__class__.__name__
    transformer = getattr(
        mappings, "DB_TO_API_%s_TRANSFORMATION" % model_name.upper()
    )

    # If count gets set, make a change to the data structure. Needed to allow
    # response to set count header based on the response data.
    count = None
    if is_list:
        # Lists return a list of tuples, [(<model_instance>, int),]
        data = []
        count = instance[0][1]
        for obj in instance:
            obj = obj[0]
            obj_data = {
                key: getattr(obj, key) for key in obj.__table__.columns.keys()
            }
            data.append(
                api_model.from_dict(transformer.apply(obj_data))
            )
    else:
        data = {
            key: getattr(
                instance, key
            ) for key in instance.__table__.columns.keys()
        }
        data = api_model.from_dict(transformer.apply(data))

    # If there is a count alter the return type to be a tuple. Tuple to return
    # ([<ApiModelInstance>, ...], <headers_dict>)
    # Required to add headers to responses.
    if count is not None:
        data = data, {"X-Total-Count": count}

    return data


def get_or_create(model, defaults=None, **identifiers):
    """Django-like helper method to get or create objects.

    The key-value pairs in identifiers are used for lookup purposes and
    the key-value pairs in defaults are used when creating a model.
    """
    defaults = defaults or {}
    instance = db.session.query(model).filter_by(**identifiers).first()
    if instance:
        return instance, False

    instance = model(**identifiers, **defaults)
    db.session.add(instance)
    db.session.commit()
    return instance, True
