# coding: utf-8

import pytest
import responses
import kiteconnect.exceptions as ex


@responses.activate
def test_wrong_json_response(kiteconnect):
    responses.add(
        responses.GET,
        "%s%s" % (kiteconnect.root, kiteconnect._routes["portfolio.positions"]),
        body="{a:b}",
        content_type="application/json"
    )
    with pytest.raises(ex.DataException) as exc:
        kiteconnect.positions()
        assert exc.message == "Couldn't parse the JSON response "\
            "received from the server: {a:b}"


@responses.activate
def test_wrong_content_type(kiteconnect):
    rdf_data = "<rdf:Description rdf:about=''><rdfs:label>zerodha</rdfs:label></rdf:Description"
    responses.add(
        responses.GET,
        "%s%s" % (kiteconnect.root, kiteconnect._routes["portfolio.positions"]),
        body=rdf_data,
        content_type="application/rdf+xml"
    )
    with pytest.raises(ex.DataException) as exc:
        kiteconnect.positions()
        assert exc.message == "Unknown Content-Type ({content_type}) with response: ({content})".format(
            content_type='application/rdf+xml',
            content=rdf_data
        )


@pytest.mark.parametrize("error_type,message", [
    ('PermissionException', 'oops! permission issue'),
    ('OrderException', 'oops! cannot place order'),
    ('InputException', 'missing or invalid params'),
    ('NetworkException', 'oopsy doopsy network issues damn!'),
    ('CustomException', 'this is an exception i just created')
])
@responses.activate
def test_native_exceptions(error_type, message, kiteconnect):
    responses.add(
        responses.GET,
        "%s%s" % (kiteconnect.root, kiteconnect._routes["portfolio.positions"]),
        body='{"error_type": "%s", "message": "%s"}' % (error_type, message),
        content_type="application/json"
    )
    with pytest.raises(getattr(ex, error_type, ex.GeneralException)) as exc:
        kiteconnect.positions()
        assert exc.message == message
