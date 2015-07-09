import os
from setuptools import setup, find_packages

# requirements
install_requires = [
	"requests"
]

# meta
setup(
	name="kiteclient",
	version="1.3.1",
	author="Kailash Nadh",
	description="Client for the Kite REST trade API",
	install_requires=install_requires,
	packages=["kiteclient"],
	download_url='https://github.com/Zerodha/kite-client.git',
)
