from typing import Union, Type, List, Optional, Dict
from mongoengine import DynamicDocument, Document
from .inject_model import inject_model

class InjectModels(object):

    def __init__(self, model: "Type[Union[DynamicDocument,Document]]", attr: str, fields: "List[str]", deleted=False, alias: "Optional[Dict]"=None):
        self.fields = fields
        self.model: "Type[Union[DynamicDocument,Document]]" = model
        self.attr = attr
        self.deleted = deleted
        self.alias = alias

    def __call__(self, req, resp, resource, params):
        try:
            data = req.context.data
            values = []
            for field in self.fields:
                value = getattr(req.context, field, None)
                if not value:
                    value = getattr(data, field, None)
                if isinstance(value, list):
                    if len(value):
                        values = values + value
                else:
                    values.append(value)
            if len(values) > 0:
                objs = self.model.objects.filter(**{[f"{self.attr}__in"]: values, "deleted" :self.deleted}).all()
            else:
                objs = []

            for field in self.fields:
                field_name = field
                if self.alias and self.alias.get(field):
                    field_name = self.alias.get(field)

                value = getattr(data, field, None)
                if isinstance(value, list):
                    setattr(req.context, field_name, list(
                        filter(lambda x: str(getattr(x, self.attr)) in list(map(lambda x: str(x), value)), objs)))
                else:
                    setattr(req.context, field_name, next(filter(lambda x: str(
                        getattr(x, self.attr)) == str(value), objs), None))
        except Exception as e:
            print(e)
            raise e