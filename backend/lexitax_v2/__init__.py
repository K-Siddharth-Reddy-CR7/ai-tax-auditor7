"""LEXITAX AUDIT v2 (research implementation, "S1").

A corrected staged pre-assessment pipeline that keeps the original tables,
landed-cost arithmetic and policy retriever of ``backend/server.py`` (which is
left unchanged) but replaces product and jurisdiction resolution with
deterministic, evidence-based rules that abstain instead of guessing.

This package is an assistive decision-support prototype. It does not make
legally authoritative classification, valuation or compliance decisions.
"""

from .config import S1Config  # noqa: F401
from .pipeline import run_s1  # noqa: F401

__version__ = "0.1.0"
