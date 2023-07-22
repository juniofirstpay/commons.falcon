import structlog
import typing

logger = structlog.get_logger(__name__)

try:
    import falcon
except ImportError as e:
    logger.warn("falcon not found")
    
import commons_falcon.errors as errors


class ApiVersioningScheme(object):
    def on_get(self, req: "falcon.Request", resp: "falcon.Request", *args, **kwargs):
        api_version: "typing.Optional[str]" = req.headers.get("X-API-VERSION")
        if not api_version:
            self.get(req, resp, *args, **kwargs)
            return

        route_handler: "typing.Callable[[falcon.Request, falcon.Response, typing.Tuple, typing.Dict], None]" = getattr(
            self, f"on_get_{api_version}", None
        )
        if not route_handler:
            raise errors.InvalidApiVersionScheme()

        route_handler(req, resp, *args, **kwargs)

    def on_post(self, req: "falcon.Request", resp: "falcon.Request", *args, **kwargs):
        api_version: "typing.Optional[str]" = req.headers.get("X-API-VERSION")
        if not api_version:
            self.post(req, resp, *args, **kwargs)
            return

        route_handler: "typing.Callable[[falcon.Request, falcon.Response, typing.Tuple, typing.Dict], None]" = getattr(
            self, f"on_post_{api_version}", None
        )
        if not route_handler:
            raise errors.InvalidApiVersionScheme()

        route_handler(req, resp, *args, **kwargs)
