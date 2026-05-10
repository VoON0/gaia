from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="mimo-smart-agent",
    version="0.1.0",
    description="A smart agent framework powered by Xiaomi MiMo-V2.5-Pro",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Your Name",
    python_requires=">=3.10",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "requests>=2.31.0",
        "pyyaml>=6.0",
        "pydantic>=2.0",
        "click>=8.0",
        "rich>=13.0",
        "httpx>=0.25.0",
        "python-dotenv>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "mimo-agent=mimo_agent.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.10",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
