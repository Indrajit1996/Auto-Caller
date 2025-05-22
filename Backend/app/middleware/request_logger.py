from __future__ import annotations

import time

from loguru import logger
from starlette.types import ASGIApp, Receive, Scope, Send


class RequestLoggerMiddleware:
    def __init__(self, app: ASGIApp, exclude_paths: list[str] | None = None) -> None:
        self.app = app
        self.exclude_paths = exclude_paths or ["/docs", "/openapi.json"]
        self.status_code_str = {
            200: "<green>200</green>",
            201: "<green>201</green>",
            204: "<green>204</green>",
            400: "<yellow>400</yellow>",
            401: "<yellow>401</yellow>",
            403: "<yellow>403</yellow>",
            404: "<yellow>404</yellow>",
            422: "<yellow>422</yellow>",
            500: "<red>500</red>",
        }
        self.method_str = {
            "GET": "<green>GET</green>",
            "POST": "<blue>POST</blue>",
            "PUT": "<yellow>PUT</yellow>",
            "PATCH": "<magenta>PATCH</magenta>",
            "DELETE": "<red>DELETE</red>",
        }

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope["path"] in self.exclude_paths:
            await self.app(scope, receive, send)
            return

        start_time = time.perf_counter()
        path = scope["path"]
        method = scope.get("method", "")

        async def send_wrapper(message: dict) -> None:
            if message["type"] == "http.response.start":
                duration = time.perf_counter() - start_time
                status = message["status"]
                duration_str = (
                    f"<cyan>{duration * 1000:.2f}ms</cyan>"
                    if duration < 0.5
                    else f"<red>{duration * 1000:.2f}ms</red>"
                )

                request_logger = logger.bind(
                    request_ip=scope.get("client", [""])[0]
                ).opt(colors=True)

                if status < 400:
                    request_logger = request_logger.info
                elif status < 500:
                    request_logger = request_logger.warning
                else:
                    request_logger = request_logger.error

                request_logger(
                    f"{self.method_str.get(method, method)} "
                    f"{path} "
                    f"{self.status_code_str.get(status, status)} "
                    f"{duration_str}"
                )
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as e:
            duration = time.perf_counter() - start_time
            logger.error(
                f"Error processing {method} {path}: {str(e)} "
                f"after {duration * 1000:.2f}ms"
            )
            raise
