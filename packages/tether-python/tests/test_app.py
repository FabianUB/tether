"""Basic tests for tether package."""

import pytest
from tether import create_app


def test_create_app():
    """Test that create_app returns a FastAPI instance."""
    app = create_app()
    assert app is not None
    assert hasattr(app, "routes")


def test_create_app_with_title():
    """Test that create_app accepts a custom title."""
    app = create_app(title="Test App")
    assert app.title == "Test App"
