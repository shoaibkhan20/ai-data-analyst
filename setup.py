from setuptools import setup, find_packages

setup(
    name="data-analyst",
    version="1.0.0",
    packages=find_packages(),
    py_modules=["cli"],
    install_requires=[],
    entry_points={
        "console_scripts": [
            "data-analyst=cli:main",
        ],
    },
)