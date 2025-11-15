"""Pytest configuration for Thermacell LIV tests."""

import builtins
import os
import sys

# Add parent directory to path before any test imports happen
parent_dir = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, parent_dir)

# Set the package name for the integration to enable relative imports
# This is critical for modules like config_flow, diagnostics, __init__ that use relative imports
package_name = os.path.basename(os.path.abspath(parent_dir))

# Monkey-patch the import system to set __package__ on imported modules
original_import = builtins.__import__


def custom_import(name, globals=None, locals=None, fromlist=(), level=0):
    """Custom import that sets __package__ for integration modules."""
    module = original_import(name, globals, locals, fromlist, level)

    # If importing one of our integration modules, set __package__
    if hasattr(module, "__file__") and module.__file__:
        module_dir = os.path.dirname(os.path.abspath(module.__file__))
        parent_dir_abs = os.path.abspath(parent_dir)

        # If this module is in our integration directory
        if module_dir == parent_dir_abs and (
            not hasattr(module, "__package__") or module.__package__ is None
        ):
            module.__package__ = package_name
            module.__name__ = f"{package_name}.{name}" if "." not in name else name

    return module


builtins.__import__ = custom_import
