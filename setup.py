"""Setup configuration for pytest to import the package properly."""

from setuptools import setup

setup(
    name="thermacell_liv",
    version="1.0.0",
    py_modules=[
        "__init__",
        "api",
        "button",
        "config_flow",
        "const",
        "coordinator",
        "diagnostics",
        "entity",
        "light",
        "repairs",
        "sensor",
        "switch",
    ],
)
