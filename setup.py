#!/usr/bin/env python

import io
import os
from codecs import open
from setuptools import setup

current_dir = os.path.abspath(os.path.dirname(__file__))

about = {}
with open(os.path.join(current_dir, "kiteconnect", "__version__.py"), "r", "utf-8") as f:
    exec(f.read(), about)

with io.open('README.md', 'rt', encoding='utf8') as f:
    readme = f.read()

setup(
    name=about["__title__"],
    version=about["__version__"],
    description=about["__description__"],
    long_description=readme,
    long_description_content_type='text/markdown',
    author=about["__author__"],
    author_email=about["__author_email__"],
    url=about["__url__"],
    download_url=about["__download_url__"],
    license=about["__license__"],
    packages=["kiteconnect"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Financial and Insurance Industry",
        "Programming Language :: Python",
        "Natural Language :: English",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: Office/Business :: Financial :: Investment",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Libraries"
    ],
    install_requires=[
        "service_identity>=18.1.0",
        "requests>=2.18.4",
        "six>=1.11.0",
        "pyOpenSSL>=17.5.0",
        "python-dateutil>=2.6.1",
        "autobahn[twisted]==19.11.2"
    ],
    tests_require=["pytest", "responses", "pytest-cov", "mock", "flake8"],
    test_suite="tests",
    setup_requires=["pytest-runner"],
    extras_require={
        "doc": ["pdoc"],
        ':sys_platform=="win32"': ["pywin32"]
    }
)
