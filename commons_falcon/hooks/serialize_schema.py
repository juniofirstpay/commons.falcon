import typing
import mongoengine as mongo
import marshmallow_objects as ms
import commons_falcon.errors as errors

class SerializeSchema(object):

    def __init__(self, schema: "typing.Type[ms.Model]", paginated=False):
        self.schema = schema
        self.paginated = paginated

    def __call__(self, req, resp, *args, **kwargs):
        try:
            data = resp.json
            if isinstance(data, list) or isinstance(data, mongo.QuerySet):
                resp.json = self.schema().dump(data, many=True)
                if self.paginated:
                    resp.json = {
                        'data': resp.json,
                        'count': resp.count,
                        'page': resp.page,
                        'page_size': resp.page_size
                    }
            elif issubclass(data.__class__, mongo.Document):
                resp.json = self.schema().dump(data)
            elif not isinstance(data, dict):
                resp.json = self.schema().dump(data)
            
        except ms.ValidationError as err:
            raise errors.DataSerializationError(err.messages)
