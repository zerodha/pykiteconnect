# coding: utf-8

"""Pytest config."""
import os
import sys
import pytest
from kiteconnect import KiteConnect

sys.path.append(os.path.join(os.path.dirname(__file__), '../helpers'))


def pytest_addoption(parser):
    """Add available args."""
    parser.addoption("--api-key", action="store", default="Api key")
    parser.addoption("--access-token", action="store", default="Access token")


def pytest_generate_tests(metafunc):
    """This is called for every test. Only get/set command line arguments. If the argument is specified in the list of test "fixturenames"."""
    access_token = metafunc.config.option.access_token
    api_key = metafunc.config.option.api_key

    if "access_token" in metafunc.fixturenames and access_token is not None:
        metafunc.parametrize("access_token", [access_token])

    if "api_key" in metafunc.fixturenames and api_key is not None:
        metafunc.parametrize("api_key", [api_key])


@pytest.fixture()
def kiteconnect(api_key, access_token):
    """Init Kite connect object."""
    return KiteConnect(api_key=api_key, access_token=access_token)
