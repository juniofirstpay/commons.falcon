import typing
import logging

logger = logging.getLogger(__name__)

try:
    import falcon
except ImportError as e:
    logger.warn("falcon module not found")


class ApplicationError(falcon.HTTPError):
    def __init__(self, title: str = None, description: str = None, *args, **kwargs):
        super(ApplicationError, self).__init__(
            getattr(self, "status", None) or falcon.HTTP_400,
            title=title
            or getattr(self.__class__, "name", None)
            or self.__class__.__name__.replace("Error", ""),
            description=description
            or getattr(self.__class__, "description", None)
            or "Some error occured",
            *args,
            **kwargs
        )


class SchemaValidationError(ApplicationError):
    name = "SchemaValidationFailed"
    description = "One or more fields don't follow schema"

    def __init__(
        self,
        fields: typing.Dict[str, typing.Any],
        description: typing.Optional[str] = None,
        code: typing.Optional[str] = "200",
    ):
        super(SchemaValidationError, self).__init__(
            title="SchemaValidationFailed", description=description, code=code
        )
        self.fields = fields

    def to_dict(self, obj_type=dict):
        result = super().to_dict(obj_type)
        result["fields"] = self.fields
        return result


class InvalidApiVersionScheme(falcon.HTTPError):
    def __init__(self, description=None, code=None):
        super().__init__(
            "404",
            title="InvalidApiVersionScheme",
            description=description or "Version for this route is not implemented",
            code=code or "100",
        )


class ObjectDoesntExistError(ApplicationError):
    name = "ObjectDoesntExist"
    description = "{object} for {parameter_type}({parameter_value}) doesn't exist"

    def __init__(
        self, object: str, parameter_type: str, parameter_value: str, *args, **kwargs
    ):
        super(ObjectDoesntExistError, self).__init__(
            title=ObjectDoesntExistError.name,
            description=ObjectDoesntExistError.description.format(
                object=object,
                parameter_type=parameter_type,
                parameter_value=parameter_value,
            ),
            *args,
            **kwargs
        )


class InvalidParameterTypeError(ApplicationError):
    name = "InvalidParameterType"
    description = "{parameter_type} is not a valid parameter for {func_name}"

    def __init__(self, parameter_type: str, func_name: str, *args, **kwargs):
        super(InvalidParameterTypeError, self).__init__(
            title=InvalidParameterTypeError.name,
            description=InvalidParameterTypeError.description.format(
                parameter_type=parameter_type, func_name=func_name
            ),
            *args,
            **kwargs
        )


class InvalidRequestParameterError(ApplicationError):
    name = "InvalidRequestParameter"
    description = "{parameter} is not a valid {parameter_type}"

    def __init__(self, parameter: str, parameter_type: str, *args, **kwargs):
        super(InvalidRequestParameterError, self).__init__(
            title=InvalidRequestParameterError.name,
            description=InvalidRequestParameterError.description.format(
                parameter=parameter, parameter_type=parameter_type
            ),
            *args,
            **kwargs
        )


class DuplicateRequestError(ApplicationError):

    name = "DuplicateRequest"
    description = (
        "Request matching with the following parameters has already been processed"
    )


class UnAuthorizedSession(ApplicationError):
    status = falcon.HTTP_401
    name = "UnAuthorizedSession"
    description = "Request is not authenticated"


class InvalidJWTError(ApplicationError):
    status = falcon.HTTP_403
    name = "InvalidJWTError"
    description = "Invalid token provided, please contact adminstrator."


class ForbiddenError(ApplicationError):
    status = falcon.HTTP_403
    name = "ForbiddenError"
    description = "Request is forbidden"


class VoucherRedeemError(ApplicationError):
    name = "VoucherRedeemViolation"
    description = "{voucher_code} is not a applicable becuse {error}"

    def __init__(self, description, *args, **kwargs):
        super(VoucherRedeemError, self).__init__(
            title=VoucherRedeemError.name, description=description, *args, **kwargs
        )

class DataSerializationError(falcon.HTTPError):

    def __init__(self, fields: typing.Dict[str, typing.Any], description: typing.Optional[str] = None, code: typing.Optional[str] = '200'):
        super().__init__(
            '400',
            title='DataSerializationFailed',
            description=description,
            code=code
        )
        self.fields = fields

    def to_dict(self, obj_type=dict):
        result = super().to_dict(obj_type)
        result['fields'] = self.fields
        return result
    
class RateLimitError(ApplicationError):
    
    status = falcon.HTTP_429
    name = "RateLimitError"
    description="Request has been blocked due to violation of resource rate limits"
    
class ServiceFailureError(ApplicationError):
    
    status = falcon.HTTP_500
    name = "ServiceFailureError"
    description = "Internal service failure"