"""Pytest configuration for Thermacell LIV tests."""

import os
import sys

# Add parent directory to path before any test imports happen
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
