"""Loads the ORIGINAL backend module (backend/server.py) without modifying it.

S1 reuses the original data tables, the landed-cost arithmetic
(``calculation_agent``) and the TF-IDF ``PolicyRetriever`` so that differences
between S0 and S1 are attributable to resolution/validation logic only.
"""
import contextlib
import importlib.util
import io
import os

_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER_PATH = os.path.join(_BACKEND_DIR, "server.py")

_server = None


def server():
    """Return the original backend module, loaded once (stdout of its loader suppressed)."""
    global _server
    if _server is None:
        spec = importlib.util.spec_from_file_location("lexitax_original_server", SERVER_PATH)
        module = importlib.util.module_from_spec(spec)
        with contextlib.redirect_stdout(io.StringIO()):
            spec.loader.exec_module(module)
        _server = module
    return _server
