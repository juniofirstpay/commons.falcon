import structlog
import json

logger = structlog.get_logger(__name__)

try:
    import falcon
except Exception as e:
    logger.warn("falcon module not found.")

class TestRoute:
    def on_get(self, req, resp):
        resp.text = json.dumps(["pong"])
        resp.status = falcon.code_to_http_status(200)