# coding: utf-8
import pytest
from mock import patch
import responses

from kiteconnect import KiteConnect
import kiteconnect.exceptions as ex


def get_fake_token(self, route, params=None):
    return {"access_token": "TOKEN"}


def get_fake_delete(self, route, params=None):
    return {"message": "token invalidated"}


class TestKiteConnectObject:

    def test_login_url(self, kiteconnect):
        assert kiteconnect.login_url() == 'https://kite.trade/connect/login?api_key=<API-KEY>'

    @responses.activate
    def test_set_session_expiry_hook_meth(self, kiteconnect):

        def mock_hook():
            raise ex.TokenException("token expired it seems! please login again")

        kiteconnect.set_session_expiry_hook(mock_hook)

        # Now lets try raising TokenException
        responses.add(
            responses.GET,
            "{0}{1}".format(kiteconnect.root, kiteconnect._routes["portfolio.positions"]),
            body='{"error_type": "TokenException", "message": "Please login again"}',
            content_type="application/json",
            status=403
        )
        with pytest.raises(ex.TokenException) as exc:
            kiteconnect.positions()
            assert exc.message == "token expired it seems! please login again"

    def test_set_access_token_meth(self, kiteconnect):
        assert kiteconnect.access_token == "<ACCESS-TOKEN>"
        # Modify the access token now
        kiteconnect.set_access_token("<MY-ACCESS-TOKEN>")
        assert kiteconnect.access_token == "<MY-ACCESS-TOKEN>"
        # Change it back
        kiteconnect.set_access_token("<ACCESS-TOKEN>")

    @patch.object(KiteConnect, "_post", get_fake_token)
    def test_get_access_token(self, kiteconnect):
        resp = kiteconnect.get_access_token(
            request_token="<REQUEST-TOKEN>",
            api_secret="<API-SECRET>"
        )
        assert resp["access_token"] == "TOKEN"
        assert kiteconnect.access_token == "TOKEN"

        # Change it back
        kiteconnect.set_access_token("<ACCESS-TOKEN>")

    @patch.object(KiteConnect, "_delete", get_fake_delete)
    def test_invalidate_token(self, kiteconnect):
        resp = kiteconnect.invalidate_token(access_token="<ACCESS-TOKEN>")
        assert resp["message"] == "token invalidated"
