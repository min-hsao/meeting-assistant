"""Setup script for Meeting Assistant"""

from setuptools import setup, find_packages

setup(
    name="meeting-assistant",
    version="0.1.0",
    description="Voice-Activated Meeting Research Assistant",
    author="Min",
    python_requires=">=3.10",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "PyAudio>=0.2.14",
        "numpy>=1.24.0",
        "faster-whisper>=0.10.0",
        "openai>=1.12.0",
        "PyQt6>=6.6.0",
        "pynput>=1.7.6",
        "pyyaml>=6.0.1",
        "python-dotenv>=1.0.0",
        "rich>=13.7.0",
    ],
    entry_points={
        "console_scripts": [
            "meeting-assistant=main:main",
        ],
    },
)
