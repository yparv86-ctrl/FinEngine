from setuptools import setup, find_packages

setup(
    name="finengine",
    version="1.0.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    entry_points={
        "console_scripts": [
            # This line links the command "finengine" to your pipeline.py file
            "finengine=finenginepy.pipeline:main",
        ],
    },
)