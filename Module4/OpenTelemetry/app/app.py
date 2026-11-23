import time
import logging

from flask import Flask

from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import (
    OTLPMetricExporter,
)
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
    OTLPSpanExporter,
)
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


# ============================================================
# Configuration
# ============================================================

OTEL_COLLECTOR_ENDPOINT = "otel-collector:4317"
SERVICE_NAME = "demo-app"


# ============================================================
# OpenTelemetry Resource
# ============================================================

resource = Resource.create(
    {
        "service.name": SERVICE_NAME,
    }
)


# ============================================================
# OpenTelemetry Tracing
# ============================================================

trace_provider = TracerProvider(resource=resource)

trace_exporter = OTLPSpanExporter(
    endpoint=OTEL_COLLECTOR_ENDPOINT,
    insecure=True,
)

trace_provider.add_span_processor(
    BatchSpanProcessor(trace_exporter)
)

trace.set_tracer_provider(trace_provider)

tracer = trace.get_tracer(SERVICE_NAME)


# ============================================================
# OpenTelemetry Metrics
# ============================================================

metric_exporter = OTLPMetricExporter(
    endpoint=OTEL_COLLECTOR_ENDPOINT,
    insecure=True,
)

metric_reader = PeriodicExportingMetricReader(
    metric_exporter
)

meter_provider = MeterProvider(
    resource=resource,
    metric_readers=[metric_reader],
)

metrics.set_meter_provider(meter_provider)

meter = metrics.get_meter(SERVICE_NAME)

request_counter = meter.create_counter(
    "http_requests_total",
    description="Total number of HTTP requests handled by the application",
)


# ============================================================
# Flask application
# ============================================================

app = Flask(__name__)

FlaskInstrumentor().instrument_app(app)
LoggingInstrumentor().instrument()

logger = logging.getLogger(__name__)

# ============================================================
# Routes
# ============================================================

@app.route("/")
def home():
    request_counter.add(1)

    logger.info("Petición recibida en /")

    with tracer.start_as_current_span("home-endpoint"):
        return "Hola desde OpenTelemetry + Docker Compose"


@app.route("/work")
def work():
    request_counter.add(1)

    logger.info("Comenzando trabajo")
    start_time = time.perf_counter()

    with tracer.start_as_current_span("leer-base-datos"):
        logger.info("Leyendo datos de la base de datos")
        time.sleep(0.2)

    with tracer.start_as_current_span("procesar-datos") as span:
        span.set_attribute("usuario.id", 123)
        span.set_attribute("operacion", "analisis")

        time.sleep(0.5)

    with tracer.start_as_current_span("guardar-resultado"):
        logger.info("Guardando resultado")
        time.sleep(0.1)

    elapsed_time = time.perf_counter() - start_time
    logger.info(f"Trabajo completado en {elapsed_time:.2f} segundos")

    return f"Trabajo completado en {elapsed_time:.2f} segundos"


@app.route("/error")
def error():
    request_counter.add(1)

    with tracer.start_as_current_span("error-endpoint") as span:
        try:
            raise ValueError("Ocurrió un error intencional")

        except Exception as exception:
            logger.error(f"Se produjo un error: intencional", exc_info=True)
            span.record_exception(exception)

            span.set_status(
                trace.Status(
                    trace.StatusCode.ERROR,
                    str(exception),
                )
            )

            return "Se produjo un error", 500


# ============================================================
# Application entry point
# ============================================================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=8080,
    )
