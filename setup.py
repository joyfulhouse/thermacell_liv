"""Setup configuration for pytest to import the package properly."""

from setuptools import find_packages, setup

setup(
    name="thermacell-liv",
    version="1.0.0",
    packages=find_packages(include=["custom_components*"]),
    python_requires=">=3.11",
)
