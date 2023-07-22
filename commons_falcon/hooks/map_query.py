import structlog
import commons_falcon.errors as errors

logger = structlog.get_logger(__name__)

try:
    import marshmallow_objects as ms
except ImportError as e:
    logger.warn("marshmallow_objects not found")

class MapQuery(object):

    def __init__(self, schema: "ms.Schema", list_fields=[]):
        self.schema = schema
        self.list_fields = list_fields

    def __call__(self, req, resp, resource, params):
        try:
            for field in self.list_fields:
                req.params[field] = req.get_param_as_list(field)
            setattr(req.context, 'data', self.schema(**req.params))
        except ms.ValidationError as err:
            raise errors.SchemaValidationError(err.messages)
