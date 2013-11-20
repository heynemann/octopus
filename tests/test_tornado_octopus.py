#!/usr/bin/env python
# -*- coding: utf-8 -*-

from preggy import expect
from mock import Mock, patch

from octopus import TornadoOctopus
from octopus.cache import Cache
from tests import TestCase


class TestTornadoOctopus(TestCase):
    def setUp(self):
        self.response = None
        self.url = None

    def test_can_create_tornado_otto(self):
        otto = TornadoOctopus()

        expect(otto.concurrency).to_equal(10)
        expect(otto.auto_start).to_be_false()
        expect(otto.cache).to_be_false()

        expect(otto.response_cache).not_to_be_null()
        expect(otto.response_cache).to_be_instance_of(Cache)
        expect(otto.response_cache.expiration_in_seconds).to_equal(30)

        expect(otto.request_timeout_in_seconds).to_equal(10)
        expect(otto.connect_timeout_in_seconds).to_equal(5)
        expect(otto.ignore_pycurl).to_be_false()

        expect(otto.running_urls).to_equal(0)
        expect(otto.url_queue).to_be_empty()

    def test_can_create_tornado_otto_with_custom_values(self):
        otto = TornadoOctopus(
            concurrency=20, auto_start=True, cache=True,
            expiration_in_seconds=60, request_timeout_in_seconds=20,
            connect_timeout_in_seconds=10, ignore_pycurl=True
        
        )

        expect(otto.concurrency).to_equal(20)
        expect(otto.auto_start).to_be_true()
        expect(otto.cache).to_be_true()

        expect(otto.response_cache).not_to_be_null()
        expect(otto.response_cache).to_be_instance_of(Cache)
        expect(otto.response_cache.expiration_in_seconds).to_equal(60)

        expect(otto.request_timeout_in_seconds).to_equal(20)
        expect(otto.connect_timeout_in_seconds).to_equal(10)
        expect(otto.ignore_pycurl).to_be_true()

        expect(otto.running_urls).to_equal(0)
        expect(otto.url_queue).to_be_empty()

    def test_can_get_response_from_tornado_response(self):
        response = Mock(
            request=Mock(
                headers={
                    'Cookie': 'foo=bar'
                },
            ),
            headers={
                'baz': 'foo'
            },
            code=200,
            body='body',
            effective_url='http://www.google.com/',
            error='error',
            request_time=2.1
        )

        otto_response = TornadoOctopus.from_tornado_response('http://www.google.com', response)

        expect(otto_response.url).to_equal('http://www.google.com')
        expect(otto_response.headers).to_be_like(response.headers)
        expect(otto_response.cookies).to_be_like({
            'foo': 'bar'
        })
        expect(otto_response.text).to_equal('body')
        expect(otto_response.error).to_equal('error')
        expect(otto_response.request_time).to_equal(2.1)

    def test_can_enqueue_url(self):
        otto = TornadoOctopus(cache=False, concurrency=0)

        otto.enqueue('http://www.google.com', None, method='GET', something="else")

        expect(otto.url_queue).to_length(1)

    @patch.object(TornadoOctopus, 'fetch')
    def test_can_enqueue_url_and_fetch(self, fetch_mock):
        otto = TornadoOctopus(cache=False)

        otto.enqueue('http://www.google.com', None, method='GET', something="else")

        expect(otto.url_queue).to_be_empty()
        fetch_mock.assert_called_once_with('http://www.google.com', None, 'GET', something='else')

    def test_can_enqueue_and_get_from_cache(self):
        mock_response = Mock()
        otto = TornadoOctopus(cache=True)
        otto.response_cache.put('http://www.google.com', mock_response)

        def response(url, response):
            self.url = url
            self.response = response

        otto.enqueue('http://www.google.com', response, method='GET', something="else")

        expect(otto.url_queue).to_be_empty()
        expect(self.response).not_to_be_null()
        expect(self.response).to_equal(mock_response)
