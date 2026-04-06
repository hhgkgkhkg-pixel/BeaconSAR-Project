"""
Setup script for Drone Drop Detection System
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="drone-drop-detection",
    version="1.0.0",
    author="Drone Detection Team",
    description="AI-powered drone safe zone detection for sensor drops",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/drone-drop-detection",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries",
        "Topic :: Multimedia :: Video",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.10",
    install_requires=[
        "opencv-python>=4.8.0",
        "numpy>=1.24.0",
        "torch>=2.0.0",
        "ultralytics>=8.0.0",
    ],
    entry_points={
        "console_scripts": [
            "drone-drop-detection=main:main",
        ],
    },
)
