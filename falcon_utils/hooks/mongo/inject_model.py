import typing
import logging
import stringcase as sc

logger = logging.getLogger(__name__)

try:
    import mongoengine as mongo
except ImportError as e:
    logger.warn("mongoengine module not found")

class inject_model(object):
    
    def __init__(self, model: "typing.Type[mongo.Document]", key: "str", callable: "typing.Callable", alias: "str"=None):
        self.model = model
        self.key = key
        self.callable = callable
        self.alias = alias
        
    def __call__(self, req, resp, resource, params):
        value = self.callable.__call__([req, resp, resource, params])
        if value is not None:
            obj = self.model.objects.filter(**{self.key: value}).first()
            setattr(req, self.alias or sc.snakecase(self.model.__name__), obj)
        
        