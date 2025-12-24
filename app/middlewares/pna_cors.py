from __future__ import annotations

from typing import Iterable, Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class PNACORSMiddleware(BaseHTTPMiddleware):
    """
    CORS + Private Network Access (PNA) support for calls coming from https://os.agno.com
    to http://localhost:* endpoints.

    Browsers may send a preflight with:
      Access-Control-Request-Private-Network: true

    To allow it, the response MUST include:
      Access-Control-Allow-Private-Network: true
    (and normal CORS headers).
    """

    def __init__(
        self,
        app,
        allow_origins: Iterable[str],
        allow_methods: Iterable[str] = ("GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"),
        allow_headers: Iterable[str] = ("*",),
        max_age: int = 600,
        allow_credentials: bool = False,
    ) -> None:
        super().__init__(app)
        self.allow_origins = set(allow_origins)
        self.allow_methods = ", ".join(allow_methods)
        self.allow_headers = ", ".join(allow_headers)
        self.max_age = str(max_age)
        self.allow_credentials = allow_credentials

    def _is_allowed_origin(self, origin: Optional[str]) -> bool:
        if not origin:
            return False
        if "*" in self.allow_origins:
            return True
        return origin in self.allow_origins

    def _set_cors_headers(self, request: Request, response: Response) -> None:
        origin = request.headers.get("origin")
        if not self._is_allowed_origin(origin):
            return

        # Echo the Origin (more compatible than "*" for many setups)
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Vary"] = "Origin"

        response.headers["Access-Control-Allow-Methods"] = self.allow_methods
        response.headers["Access-Control-Allow-Headers"] = self.allow_headers
        response.headers["Access-Control-Max-Age"] = self.max_age

        if self.allow_credentials:
            response.headers["Access-Control-Allow-Credentials"] = "true"

        # --- PNA support ---
        # If browser is requesting private network access in preflight, allow it.
        if request.headers.get("access-control-request-private-network") == "true":
            response.headers["Access-Control-Allow-Private-Network"] = "true"

    async def dispatch(self, request: Request, call_next):
        # Handle preflight early
        if request.method.upper() == "OPTIONS" and request.headers.get("origin"):
            response = Response(status_code=200)
            self._set_cors_headers(request, response)
            return response

        response = await call_next(request)
        self._set_cors_headers(request, response)
        return response
