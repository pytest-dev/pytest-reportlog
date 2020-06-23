from io import open

from setuptools import setup, find_packages

with open("README.rst", encoding="utf-8") as f:
    readme = f.read()

setup(
    name="pytest-reportlog",
    entry_points={"pytest11": ["pytest_reportlog = pytest_reportlog.plugin"]},
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    platforms="any",
    python_requires=">=3.5",
    install_requires=["pytest>=5.2"],
    use_scm_version={"write_to": "src/pytest_reportlog/_version.py"},
    setup_requires=["setuptools_scm"],
    url="https://github.com/pytest-dev/pytest-reportlog",
    license="MIT",
    author="Bruno Oliveira",
    author_email="nicoddemus@gmail.com",
    description="Replacement for the --resultlog option, focused in simplicity and extensibility",
    long_description=readme,
    keywords="pytest",
    extras_require={"dev": ["pre-commit", "tox"]},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Framework :: Pytest",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: Software Development :: Testing",
    ],
)
