import os
from setuptools import setup, find_packages

# requirements
install_requires = [
	"requests"
]

# meta
setup(
	name="Kite Connect  Client",
	version="2.1",
	author="Kailash Nadh",
	description="Client for the Kite Connect",
	install_requires=install_requires,
	packages=["kiteclient"]
)
