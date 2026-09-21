"""Compatibility wrapper for the canonical FastAPI application."""
from agents.api import app


def create_app():
    return app
