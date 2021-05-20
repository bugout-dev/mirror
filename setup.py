import os
from importlib.machinery import SourceFileLoader
from pkg_resources import parse_requirements
from setuptools import find_packages, setup

MODULE_NAME = "bugout_mirror"

module = SourceFileLoader(
    MODULE_NAME, os.path.join(MODULE_NAME, "__init__.py")
).load_module()

long_description = ""
with open("README.md") as ifp:
    long_description = ifp.read()

setup(
    name=MODULE_NAME,
    version=module.__version__,
    author=module.__author__,
    author_email=module.__email__,
    license=module.__license__,
    description=module.__description__,
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/bugout-dev/bugout-python",
    platforms="all",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: Implementation :: CPython",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.5",
    packages=find_packages(),
    package_data={"bugout": ["py.typed"]},
    zip_safe=False,
    install_requires=[
        "click",
        "pydantic",
        "requests",
        "tqdm",
    ],
    extras_require={"dev": ["black", "mypy", "jupyter"]},
    entry_points={"console_scripts": ["{0} = {0}.cli:cli".format(MODULE_NAME)]},
)
