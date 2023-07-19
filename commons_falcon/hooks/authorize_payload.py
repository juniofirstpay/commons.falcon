import typing
import logging
import commons_falcon.auth as auth_utils
import commons_falcon.errors as errors

logger = logging.getLogger(__name__)

try:
    import falcon
except Exception as e:
    logger.warn("falcon module not found")


class AuthorizePayload:
    def __init__(
        self,
        callable: typing.Callable[
            [typing.Tuple["falcon.Request", "falcon.Response", typing.Any, typing.Dict]], str
        ],
        level: "auth_utils.AccessLevel",
    ) -> None:
        self.callable = callable
        self.level = level

    def __call__(
        self, req: "falcon.Request", resp: "falcon.Response", resource, params: "typing.Dict"
    ) -> None:
        authorization_scheme = req.context.get("authorization_scheme")
        if authorization_scheme != auth_utils.AuthorizationScheme.JWT:
            return
        
        authorization_payload = req.context.get("authorization_payload")
        if authorization_payload == None:
            raise errors.UnAuthorizedSession()

        value = self.callable((req, resp, resource, params))
        if value == None:
            raise errors.UnAuthorizedSession()

        profiles = authorization_payload.get("profiles")
        person_ids = {
            auth_utils.AccessLevel.SELF: profiles.get("self", []),
            auth_utils.AccessLevel.DEPENDANT: profiles.get("dependants", []),
            auth_utils.AccessLevel.SELF_AND_DEPENDANT: profiles.get("self", [])
            + profiles.get("dependants", []),
        }

        if value in person_ids[self.level]:
            return

        raise errors.UnAuthorizedSession()
