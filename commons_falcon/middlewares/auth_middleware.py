import typing
import falcon
import datetime
import commons_falcon.errors as errors
import commons_falcon.auth as auth_utils


class SimpleAuthMiddleware(object):
    def __init__(self, config: dict, oauth_client=None, jwt_auth_service=None):
        self.__config = config
        self.__oauth_client = oauth_client
        self.__jwt_auth_service = jwt_auth_service

        self.__config["exempted_paths"] = self.__config.get("exempted_paths", [])
        self.__config["clients"] = self.__config.get("clients", {})
        self.__config["api_keys"] = self.__config.get("api_keys", [])
        self.__config["ip_whitelist"] = self.__config.get("ip_whitelist", [])

    def process_request(self, req: "falcon.Request", resp: "falcon.Response") -> object:
        self.request_initate_time = datetime.datetime.utcnow()

        if req.method == "OPTIONS":
            resp.status = falcon.HTTP_200
            resp.complete = True
            return
        
        jwt_auth = req.headers.get("X-JWT", None)
        if jwt_auth:
            verification_error, token = self.__jwt_auth_service.verify(jwt_auth)
            if verification_error:
                error_mapping = {
                    auth_utils.JWTVerificationError.EXPIRED: errors.InvalidJWTError,
                    auth_utils.JWTVerificationError.INVALID: errors.UnAuthorizedSession,
                    auth_utils.JWTVerificationError.INTERNAL: errors.ServiceFailureError,
                }

                raise error_mapping.get(verification_error, errors.UnAuthorizedSession)()

            req.context["authorization_scheme"] = auth_utils.AuthorizationScheme.JWT
            req.context["authorization_payload"] = token
            return

        if req.access_route[0] in self.__config.get("ip_whitelist"):
            req.context["authorization_scheme"] = auth_utils.AuthorizationScheme.IP_WHITELIST
            return

        if req.headers.get("X-API-KEY") in self.__config.get("api_keys"):
            req.context["authorization_scheme"] = auth_utils.AuthorizationScheme.API_KEY
            return

        client_id, client_secret = (
            req.headers.get("CLIENT-ID") or req.headers.get("CLIENTID"),
            req.headers.get("CLIENT-SECRET") or req.headers.get("CLIENTSECRET"),
        )
        if (
            (self.__config.get("clients") or {}).get(client_id) == client_secret
            and client_id is not None
            and client_secret is not None
        ):
            req.context["authorization_scheme"] = auth_utils.AuthorizationScheme.CLIENT_SECRET
            return

        auth = req.headers.get("AUTHORIZATION", None)
        if auth and len(auth) > 0:
            auth_token_string = auth[7:]
            error, token = self.__oauth_client.introspection(
                None, None, auth_token_string, "access_token"
            )
            if error:
                raise errors.UnAuthorizedSession()

            error, oauth_user = self.__oauth_client.get_user(
                auth_token=auth_token_string
            )
            if error or not oauth_user.get("username"):
                raise errors.UnAuthorizedSession()

            setattr(req, "user", oauth_user)
            req.context["authorization_scheme"] = auth_utils.AuthorizationScheme.ACCESS_TOKEN
            return

    def process_resource(
        self, req: "falcon.Request", resp: "falcon.Response", resource, params
    ):
        """
        Validate whethter the resource has specified any authorization schemes
        to be validated against and was that authorization scheme added by `process_request`.
        `AuthorizationScheme.EXEMPTED_PATH is a special case and handled separately,
        this is because `process_request` does not provide with `uri_template` which is
        being used to match the route in `self.__config.get('exempted_paths')` list.
        """
        request_authorization_scheme: "typing.Optional[auth_utils.AuthorizationScheme]" = req.context.get(
            "authorization_scheme", None
        )
        resource_authorization_schemes: "typing.List[auth_utils.AuthorizationScheme]" = getattr(
            resource, "authorization_schemes", []
        )

        if len(resource_authorization_schemes) == 0:
            return

        if request_authorization_scheme is None:
            if req.uri_template not in self.__config.get("exempted_paths"):
                raise errors.UnAuthorizedSession()

            req.context["authorization_scheme"] = auth_utils.AuthorizationScheme.EXEMPTED_PATH

        if request_authorization_scheme == auth_utils.AuthorizationScheme.EXEMPTED_PATH:
            # Adding a shortcut for anonymous authorization
            return

        if request_authorization_scheme is None:
            raise errors.UnAuthorizedSession()

        if request_authorization_scheme not in resource_authorization_schemes:
            raise errors.ForbiddenError()

    def process_response(self, req, resp, resource, params):
        pass
