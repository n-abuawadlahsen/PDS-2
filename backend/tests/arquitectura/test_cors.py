"""SPEC 02 S2.2.6: `allow_origins=["*"]` esta prohibido."""

from __future__ import annotations

from app.main import app


def test_cors_no_usa_wildcard():
    middlewares_cors = [m for m in app.user_middleware if m.cls.__name__ == "CORSMiddleware"]
    assert middlewares_cors, "no se encontro CORSMiddleware"
    for middleware in middlewares_cors:
        origenes = middleware.kwargs.get("allow_origins", [])
        assert "*" not in origenes
        assert middleware.kwargs.get("allow_credentials") is True
