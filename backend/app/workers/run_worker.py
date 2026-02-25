"""
Cloud Run compatible arq worker runner.

Runs the arq worker in a thread alongside a minimal HTTP health server
so Cloud Run's health check passes.

Upstash Redis aggressively drops idle connections which crashes the arq
polling loop.  We wrap the worker in an infinite retry loop so it
automatically reconnects instead of letting the container die.
"""
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

import structlog

logger = structlog.get_logger()

_MAX_BACKOFF_SECONDS = 30
_INITIAL_BACKOFF_SECONDS = 2


class HealthHandler(BaseHTTPRequestHandler):
    """Minimal health check handler for Cloud Run."""

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"status":"worker-running"}')

    def log_message(self, fmt, *args):
        pass


def run_health_server():
    """Run health HTTP server on PORT (default 8080)."""
    import os
    port = int(os.environ.get("PORT", "8080"))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    logger.info("Worker health server started", port=port)
    server.serve_forever()


def main():
    health_thread = threading.Thread(target=run_health_server, daemon=True)
    health_thread.start()

    from arq import run_worker

    from app.workers.image_worker import WorkerSettings

    backoff = _INITIAL_BACKOFF_SECONDS
    while True:
        try:
            logger.info("Starting arq worker...")
            run_worker(WorkerSettings)
            logger.warning("Arq worker exited normally — restarting in %ds", backoff)
        except KeyboardInterrupt:
            logger.info("Worker interrupted — shutting down")
            break
        except Exception as exc:
            logger.error(
                "Arq worker crashed — restarting",
                error=str(exc),
                backoff_seconds=backoff,
            )

        time.sleep(backoff)
        backoff = min(backoff * 2, _MAX_BACKOFF_SECONDS)


if __name__ == "__main__":
    main()
