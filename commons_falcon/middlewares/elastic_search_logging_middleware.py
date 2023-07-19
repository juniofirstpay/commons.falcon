import logging
import traceback
import falcon
import json
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    import elasticsearch as esc
except ImportError as e:
    logger.warn("ElasticSearch is not found.")

try:
    import flatten_json as fj
except ImportError as e:
    logger.warn("flatten_json module not found")


class ESLoggingMiddleware:
    def __init__(
        self,
        host: "str" = None,
        port: "str" = None,
        username: "str" = None,
        password: "str" = None,
        scheme: "str" = "http",
        request_timeout: "int" = 5,
        index: "str" = None,
    ):
        es = esc.Elasticsearch(
            [host],
            port=port,
            http_auth=(username, password),
            scheme=scheme,
            request_timeout=request_timeout,
            max_retries=1,
        )

        self.logger = lambda doc: es.index(
            index=index, id=int(datetime.utcnow().timestamp() * 1000000), body=doc
        )

    def process_request(self, req, resp):
        setattr(req, "start_time", datetime.utcnow())
        setattr(req, "es_doc", {})
        if getattr(req, "es_doc") is not None:
            req.es_doc["req.remote_addr"] = req.access_route[0]
            req.es_doc["req.datetime"] = datetime.utcnow().timestamp()
            req.es_doc["req.method"] = req.method

    def process_resource(self, req, resp, resource, params):
        try:
            if getattr(req, "es_doc") is not None:
                req.es_doc["req.path"] = req.path
                req.es_doc["req.name"] = resource.__class__.__name__
                if params:
                    for key, value in params.items():
                        req.es_doc["req.params." + key] = value
        except Exception as e:
            logger.error(e)

    def process_response(self, req, resp, resource, res_succeeded):
        try:
            if getattr(req, "es_doc") is not None and (
                getattr(resp, "json", None) is not None
                or getattr(resp, "data", None) is not None
            ):
                req.es_doc["resp.status_code"] = resp.status
                req.es_doc["resp.content_length"] = resp.content_length
                resp_json = {}
                try:
                    if resp.status != falcon.HTTP_200:
                        resp_json = json.loads(resp.data or "{}")

                        error = fj.flatten(resp_json)
                        for key, value in error.items():
                            req.es_doc["resp.error." + key] = value

                        req.es_doc["resp.error.traceback"] = getattr(
                            req, "error_traceback", None
                        )
                except Exception as e:
                    logger.error(json.dumps(resp_json))
                    logger.error(traceback.format_exc())

            if getattr(req, "es_doc") is not None:
                try:
                    self.logger(req.es_doc)
                except Exception as e:
                    logger.error(e)
        except Exception as e:
            logger.error(e)
