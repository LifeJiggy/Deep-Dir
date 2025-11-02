#!/usr/bin/env python3
"""
Setup script for DeepDir - Advanced Directory Enumeration Tool
"""

from setuptools import setup, find_packages
import os
from pathlib import Path

# Read the contents of README file
this_directory = Path(__file__).parent
try:
    long_description = (this_directory / "README.md").read_text(encoding='utf-8')
except UnicodeDecodeError:
    long_description = (this_directory / "README.md").read_text(encoding='latin-1')

# Read requirements
def read_requirements():
    with open("requirements.txt", "r") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]

# Version
__version__ = "5.0.0"

setup(
    name="deepdir",
    version=__version__,
    author="ArkhAngelLifeJiggy",
    author_email="Bloomtonjovish@gmail.com",
    description="Advanced Directory Enumeration Tool - More powerful than dirsearch and gospider",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/LifeJiggy/Deep-Dir.git",
    project_urls={
        "Bug Reports": "https://github.com/LifeJiggy/Deep-Dir/issues",
        "Source": "https://github.com/LifeJiggy/Deep-Dir.git",
        "Documentation": "https://github.com/LifeJiggy/Deep-Dir#readme",
    },
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Information Technology",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Security",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: System :: Networking",
        "Topic :: Utilities",
    ],
    keywords="directory enumeration brute-force web-security penetration-testing reconnaissance",
    python_requires=">=3.9",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=6.0.0",
            "pytest-cov>=2.0.0",
            "black>=21.0.0",
            "flake8>=3.9.0",
            "mypy>=0.800",
        ],
        "docs": [
            "sphinx>=4.0.0",
            "sphinx-rtd-theme>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "deepdir=deepdir:main",
        ],
    },
    zip_safe=False,
)