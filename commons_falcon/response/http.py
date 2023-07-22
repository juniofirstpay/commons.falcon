import structlog
import typing

logger = structlog.get_logger(__name__)

try:
    import requests
except ImportError as e:
    logger.warn("Requests module not found.")

try:
    import marshmallow_objects as ms
except ImportError as e:
    logger.warn("marshmallow_objects module not found.")

def process_result_with_code(result: requests.Response,
                             req_log_obj=None,
                             schema: typing.Optional[typing.Type[ms.Schema]] = None) -> typing.Tuple[int, typing.Union[dict, str]]:
    response = {}
    if result.status_code == 200:
        if schema is not None:
            response = schema(**result.json())
        else:
            response = result.json()
    elif result.status_code >= 400:
        try:
            response = result.json()
        except Exception as e:
            response = {"error": result.text}

    return result.status_code, response