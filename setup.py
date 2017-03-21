from setuptools import setup, find_packages
from logserver import __version__

with open("README.rst", 'r') as f:
    readme = f.read()


setup(
    name="logserver",
    version=__version__,
    author="Michael V. DePalatis",
    author_email="mike@depalatis.net",
    description="Reusable, dependency-free log server backed by SQLite",
    long_description=readme,
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6"
    ]
)
