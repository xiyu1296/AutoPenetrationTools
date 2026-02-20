from setuptools import setup, find_packages

setup(
    name="autoattack-tools",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "fastapi>=0.129.0",
        "fastapi-cdn-host>=0.10.0",
        "uvicorn>=0.41.0",
        "pydantic>=2.12.5",
    ],
    entry_points={
        "console_scripts": [
            "autoattack-tools=app:main",
        ],
    },
)
