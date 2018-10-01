#!/usr/bin/env python

import io
import os
import sys
import warnings
import distutils.util
from codecs import open
from setuptools import setup, Command
from setuptools.command.install import install as _install

current_dir = os.path.abspath(os.path.dirname(__file__))

about = {}
with open(os.path.join(current_dir, "kiteconnect", "__version__.py"), "r", "utf-8") as f:
    exec(f.read(), about)

# Public URL to download windows wheel
public_wheels_path = "https://raw.githubusercontent.com/zerodhatech/python-wheels/master/{wheel_name}"
# Twisted package wheel name
twisted_wheel_name = "Twisted-18.7.0-cp{version}-cp{version}m-{platform}.whl"
# Available python versions for Twisted package
twisted_py_versions = ["34", "35", "36", "37"]


# Install package using pip
def pip_install(pkg):
    os.system("pip install " + pkg)


class install(_install):
    def run(self):
        # Service identity has to be installed before twisted.
        pip_install("service-identity>=17.0.0")
        py_version = "{}{}".format(sys.version_info.major, sys.version_info.minor)

        # Check if platform is Windows and package for Python version is available
        # Currently python version with enable unicode UCS4 is not supported
        if os.name == "nt" and sys.version_info.major > 2 and py_version in twisted_py_versions:
            # Install twisted wheels for windows
            platform = distutils.util.get_platform().replace("-", "_")
            wheel_name = twisted_wheel_name.format(version=py_version, platform=platform)
            pip_install(public_wheels_path.format(wheel_name=wheel_name))
        else:
            # Install from Pypi for other platforms
            pip_install("Twisted>=17.9.0")

        _install.do_egg_install(self)


class FakeBdist(Command):
    """Fake bdist wheel class for ignoring bdist_wheel build
    """

    user_options = [(
        "dist-dir=",
        "d",
        "directory to put final built distributions in [default: dist]"
    ), (
        "python-tag=",
        None,
        "Python tag (cp32|cp33|cpNN) for abi3 wheel tag (default:false)"
    )]

    def initialize_options(self):
        self.dist_dir = None
        self.python_tag = None

    def finalize_options(self):
        pass

    def run(self):
        warnings.warn(
            "{name}{version} does not support building wheels".format(
                name=about["__title__"],
                version=about["__version__"]
            )
        )


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
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Topic :: Office/Business :: Financial :: Investment",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Libraries"
    ],
    install_requires=[
        "requests>=2.18.4",
        "six>=1.11.0",
        "pyOpenSSL>=17.5.0",
        "enum34>=1.1.6",
        "python-dateutil>=2.6.1",
        "autobahn[twisted]>=17.10.1"
    ],
    tests_require=["pytest", "responses", "pytest-cov", "mock", "flake8"],
    test_suite="tests",
    setup_requires=["pytest-runner"],
    extras_require={
        "doc": ["pdoc"],
        ':sys_platform=="win32"': ["pypiwin32<=220"]
    },
    cmdclass={"install": install, "bdist_wheel": FakeBdist}
)
