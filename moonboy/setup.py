from setuptools import setup, find_packages

setup(
    name="moonboy",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        # Add your dependencies here
        "numpy",
        "pandas",
        "scikit-learn",
        "torch",
        "yfinance",
        "polygon-api-client",
        "pyyaml",
    ],
) 