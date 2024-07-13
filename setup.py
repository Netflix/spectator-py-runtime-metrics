import os

from setuptools import setup


def read(fname):
    """Utility function to read a file, for publishing the README with the package."""
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name="netflix-spectator-py-runtime-metrics",
    version="1.0.0rc0",
    python_requires=">3.9",
    description="Library to collect runtime metrics for Python applications using spectator-py.",
    long_description=read("README.md"),
    long_description_content_type="text/markdown",
    author="Netflix Telemetry Engineering",
    author_email="netflix-atlas@googlegroups.com",
    license="Apache 2.0",
    url="https://github.com/Netflix/spectator-py-runtime-metrics",
    packages=["runmetrics"],
    install_requires=["netflix-spectator-py==1.0.0rc1"],
    extras_require={
        "dev": [
            "check-manifest",
            "pylint",
            "pytest-cov",
            "pytest"
        ]
    }
)
