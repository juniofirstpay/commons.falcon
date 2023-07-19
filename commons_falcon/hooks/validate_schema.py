import typing
import logging
import commons_falcon.errors as errors

logger = logging.getLogger(__name__)

try:
    import marshmallow_objects as ms
except ImportError:
    logger.warn("marshmallow_objects module not found")


class ValidateSchema(object):

    def __init__(self, schema: "typing.Type[ms.Model]", list=False):
        self.schema= schema
        self.list = list

    def __call__(self, req, resp, resource, params):
        try:
            data = req.json
            if self.list:
                req.context['data'] = self.schema(many=True).load(data)
            else:
                req.context['data'] = self.schema(**data)
        except ms.ValidationError as err:
            raise errors.SchemaValidationError(err.messages)


class ValidateParams(object):

    def __init__(self, schema: "typing.Type[ms.Model]"):
        self.schema = schema

    def __call__(self, req, resp, resource, params):
        try:
            req.context['params'] = self.schema(**params)
        except ms.ValidationError as err:
            errors.SchemaValidationError(err.messages)