"""
web/__init__.py
================
Web interface package for WikiMolGen.

This package provides a modular Streamlit-based web interface
for generating molecular structures.
"""

from wikimolgen import __version__  # noqa: F401

__all__ = [
    "rendering",
    "session",
    "template",
    "ui",
    "wikipedia",
]
