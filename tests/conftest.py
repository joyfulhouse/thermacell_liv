"""Pytest configuration for Thermacell LIV tests."""

import os
import sys

# Add parent directory to path before any test imports happen
# This allows direct imports when running locally without installation
parent_dir = os.path.join(os.path.dirname(__file__), "..")
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
