import structlog
import time

logger = structlog.get_logger(__name__)

try:
    from prometheus_client import Counter
except ImportError as e:
    logger.warn("prometheus_client not found")

try:
    from falcon_prometheus import PrometheusMiddleware
except ImportError as e:
    logger.warn("falcon_prometheus not found")


class PrometheusMiddlewareCustom(PrometheusMiddleware):
    def __init__(self, *args, **kwargs):
        super(PrometheusMiddlewareCustom, self).__init__(*args, **kwargs)
        self.costom_counter = Counter(
            "api_counter",
            "API Call Counter",
            ["worker", "api_name"],
            registry=self.registry,
        )

    def process_request(self, req, resp):
        setattr(req, "start_time", time.time())

    def process_response(self, req, resp, resource, req_succeeded):
        resp_time = time.time() - req.start_time
        resource_class = resource.__class__.__name__
        self.requests.labels(
            method=req.method, path=resource_class, status=resp.status
        ).inc()
        self.request_historygram.labels(
            method=req.method, path=resource_class, status=resp.status
        ).observe(resp_time)

    def inc_counter(self, name, value=1, **labels):
        self.costom_counter.labels(api_name=name, **labels).inc(value)


PROMETHEUS_MIDDLEWARE = PrometheusMiddlewareCustom()
