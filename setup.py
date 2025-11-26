from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    readme = f.read()

setup(
    name="nala-accelerator",  # must match pyproject.toml
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "pydantic>=2",
        "pyyaml>=6",
        "numpy>=1.26",
        "scipy>=1.15",
        "munch>=4",
    ],
    python_requires=">=3.10",
    long_description=readme,
    long_description_content_type="text/markdown",
)

