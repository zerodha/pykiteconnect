import os
from setuptools import setup, find_packages

# requirements
install_requires = [
	"requests"
]

# meta
setup(
	name="Kite Trade (REST) Client",
	version="1.3",
	author="Kailash Nadh",
	description="Client for the Kite REST trade API",
	install_requires=install_requires,
	packages=["kiteclient"]
)