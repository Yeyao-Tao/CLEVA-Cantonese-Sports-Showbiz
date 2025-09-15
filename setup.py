#!/usr/bin/env python3
"""
Setup script for CLEVA Cantonese Sports Showbiz package.
"""

from setuptools import setup, find_packages

setup(
    name="cleva-cantonese",
    version="0.1.0",
    description="CLEVA Cantonese Sports and Showbiz benchmark tools",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=[
        # Add your dependencies here from requirements.txt
    ],
    entry_points={
        "console_scripts": [
            # Add command-line scripts here if needed
        ],
    },
)
