from fastapi import APIRouter
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

router = APIRouter()

REQS = Counter("http_requests_total", "Total HTTP requests", ["route", "method", "status"])
LAT = Histogram("http_request_latency_seconds", "Request latency", ["route"])


@router.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
