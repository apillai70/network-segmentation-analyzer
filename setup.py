from setuptools import setup, find_packages

# Read README with UTF-8 encoding to avoid Windows encoding issues
with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="network-segmentation-analyzer",
    version="1.0.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "pandas>=2.0.0",
        "numpy>=1.24.0",
        "networkx>=3.0",
        "scikit-learn>=1.3.0",
    ],
    python_requires=">=3.8",
    author="Your Team",
    description="Enterprise Network Segmentation Analysis with ML/DL",
    long_description=long_description,
    long_description_content_type="text/markdown",
)