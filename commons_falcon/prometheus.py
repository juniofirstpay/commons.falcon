import structlog
from time import perf_counter
from prometheus_client import multiprocess
from prometheus_client import CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST, Counter, Summary


logger = structlog.get_logger(__name__)

registry = None
middleware = None
route = None
metrics = None

def configure_falcon_prometheus(multiprocess=False):
    global registry
    global middleware
    global metrics
    global route

    registry = CollectorRegistry()

    if multiprocess:
        multiprocess.MultiProcessCollector(registry)

    NUM_INCOMING_REQUESTS = Counter("http_incoming_requests", "Total HTTP Requests", labelnames=["method", "path", "host"])  
    NUM_INCOMING_PROCESSED_REQUESTS = Counter("http_incoming_processed_requests", "Total HTTP Requests Processed", labelnames=["method", "path", "host", "status"])
    REQUEST_TIME = Summary('http_incoming_requests_processing_seconds', 'Time spent processing request', labelnames=["method", "path", "host", "status"])
    REQUEST_PAYLOAD_SIZE = Summary('http_incoming_requests_payload_size', 'Request Payload Size', labelnames=["method", "path", "host", "status"])

    class PrometheusMiddleware():

        def process_request(self, req: "falcon.Request", *args, **kwargs):
            NUM_INCOMING_REQUESTS.labels(method=req.method, path=req.path, host=req.host).inc()
            req.start_time = perf_counter()
            

        def process_response(self, req: "falcon.Response", resp: "falcon.Response", resource: "object", req_succeeded: "bool"):
            NUM_INCOMING_PROCESSED_REQUESTS.labels(method=req.method, path=req.path, host=req.host, status=resp.status)
            REQUEST_TIME.labels(method=req.method, path=req.path, host=req.host, status=resp.status).observe(perf_counter() - req.start_time)
            REQUEST_PAYLOAD_SIZE.labels(method=req.method, path=req.path, host=req.host, status=resp.status).observe(len(resp.body or []))

    class MetricsRoute():

        def on_get(self, req: "falcon.Request", resp: "falcon.Response", *args, **kwargs):
            data = generate_latest(registry)
            logger.debug(data)

            resp.headers["Content-Type"] = CONTENT_TYPE_LATEST
            resp.content_type = CONTENT_TYPE_LATEST
            resp.data = data



    middleware = PrometheusMiddleware
    metrics = {
        'NUM_INCOMING_REQUESTS': NUM_INCOMING_PROCESSED_REQUESTS,
        'NUM_INCOMING_PROCESSED_REQUESTS': NUM_INCOMING_PROCESSED_REQUESTS,
        'REQUEST_TIME': REQUEST_TIME,
        'REQUEST_PAYLOAD_SIZE': REQUEST_PAYLOAD_SIZE,
    }
    route = MetricsRoute