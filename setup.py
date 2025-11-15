"""Setup configuration for pytest to import the package properly."""

from setuptools import find_packages, setup

setup(
    name="thermacell-liv",
    version="1.0.0",
    packages=find_packages(where="."),
    package_dir={"": "."},
    python_requires=">=3.11",
)
