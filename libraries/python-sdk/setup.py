from setuptools import setup, find_packages
from pathlib import Path
import os

# Get long description from README if it exists
readme_file = Path(__file__).parent / "README.md"
long_description = ""
if readme_file.exists():
    try:
        with open(readme_file, "r", encoding="utf-8") as fh:
            long_description = fh.read()
    except Exception:
        pass

# Simple setup without complex metadata
setup(
    name="gennet-sdk",
    version="1.0.0",
    description="Python SDK for GenNet Cloud Platform",
    long_description=long_description if long_description else "Python SDK for GenNet Cloud Platform",
    long_description_content_type="text/markdown" if long_description else None,
    packages=find_packages(exclude=["tests", "tests.*", "*.tests", "*.tests.*"]),
    py_modules=[],
    python_requires=">=3.10",
    install_requires=[
        "requests>=2.31.0",
        "pandas>=2.0.0",
        "numpy>=1.24.0",
    ],
    zip_safe=False,
)

