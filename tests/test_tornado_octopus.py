#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

from preggy import expect
from mock import Mock, patch

from octopus import TornadoOctopus
from octopus.cache import Cache
from tests import TestCase


class TestTornadoOctopus(TestCase):
    def setUp(self):
        self.response = None
        self.url = None
        self.responses = {}

    def get_response(self, request=None):
        if request is None:
            request = Mock(
                headers={
                    'Cookie': 'foo=bar'
                },
            )

        return Mock(
            request=request,
            headers={
                'baz': 'foo'
            },
            code=200,
            body='body',
            effective_url='http://www.google.com/',
            error='error',
            request_time=2.1
        )

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

    def test_can_get_queue_info(self):
        otto = TornadoOctopus()

        expect(otto.queue_size).to_equal(0)
        expect(otto.is_empty).to_be_true()

    def test_can_get_response_from_tornado_response(self):
        response = self.get_response()

        otto_response = TornadoOctopus.from_tornado_response('http://www.google.com', response)

        expect(otto_response.url).to_equal('http://www.google.com')
        expect(otto_response.headers).to_be_like(response.headers)
        expect(otto_response.cookies).to_be_like({
            'foo': 'bar'
        })
        expect(otto_response.text).to_equal('body')
        expect(otto_response.error).to_equal('error')
        expect(otto_response.request_time).to_equal(2.1)

    def test_can_get_response_from_tornado_response_when_no_cookies(self):
        response = self.get_response(request=Mock(headers={}))

        otto_response = TornadoOctopus.from_tornado_response('http://www.google.com', response)

        expect(otto_response.url).to_equal('http://www.google.com')
        expect(otto_response.headers).to_be_like(response.headers)
        expect(otto_response.cookies).to_be_empty()
        expect(otto_response.text).to_equal('body')
        expect(otto_response.error).to_equal('error')
        expect(otto_response.request_time).to_equal(2.1)

    def test_can_enqueue_url(self):
        otto = TornadoOctopus(cache=False, concurrency=0)

        otto.enqueue('http://www.google.com', None, method='GET', something="else")

        expect(otto.url_queue).to_length(1)

    @patch.object(TornadoOctopus, 'fetch')
    def test_can_enqueue_url_and_fetch(self, fetch_mock):
        otto = TornadoOctopus(cache=True)

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

    def test_can_fetch(self):
        otto = TornadoOctopus(cache=False, auto_start=True)
        otto.response_cache.put('http://www.google.com', Mock())

        http_client_mock = Mock()
        otto.http_client = http_client_mock

        otto.fetch('http://www.google.com', None, 'GET')

        expect(otto.running_urls).to_equal(1)
        expect(http_client_mock.fetch.called).to_be_true()

    def test_fetch_gets_the_response_from_cache_if_available(self):
        otto = TornadoOctopus(cache=True, auto_start=True)
        response_mock = Mock()
        otto.response_cache.put('http://www.google.com', response_mock)

        http_client_mock = Mock()
        otto.http_client = http_client_mock

        callback = Mock()

        otto.fetch('http://www.google.com', callback, 'GET')

        expect(otto.running_urls).to_equal(1)
        expect(http_client_mock.fetch.called).to_be_false()
        callback.assert_called_once_with('http://www.google.com', response_mock)

    @patch.object(TornadoOctopus, 'stop')
    def test_handle_request(self, stop_mock):
        otto = TornadoOctopus(cache=False, auto_start=True)

        response = self.get_response()

        callback = Mock()

        handle_request = otto.handle_request('some url', callback)

        handle_request(response)

        expect(otto.running_urls).to_equal(-1)
        expect(callback.called).to_be_true()
        expect(stop_mock.called).to_be_true()

    @patch.object(TornadoOctopus, 'stop')
    def test_handle_request_when_queue_has_no_items(self, stop_mock):
        otto = TornadoOctopus(cache=True, auto_start=True)
        otto.response_cache = Mock()

        response = self.get_response()

        callback = Mock()

        handle_request = otto.handle_request('some url', callback)

        handle_request(response)

        expect(otto.running_urls).to_equal(-1)
        expect(callback.called).to_be_true()
        expect(stop_mock.called).to_be_true()
        expect(otto.response_cache.put.called).to_be_true()

    def test_handle_request_when_queue_has_no_items_but_running_urls(self):
        otto = TornadoOctopus(cache=True, auto_start=True)
        otto.response_cache = Mock()
        otto.running_urls = 10

        response = self.get_response()

        callback = Mock()

        handle_request = otto.handle_request('some url', callback)

        handle_request(response)

        expect(otto.running_urls).to_equal(9)
        expect(callback.called).to_be_true()
        expect(otto.response_cache.put.called).to_be_true()

    @patch.object(TornadoOctopus, 'fetch')
    def test_handle_request_when_queue_has_items(self, fetch_mock):
        otto = TornadoOctopus(cache=False, auto_start=True)

        handler_mock = Mock()

        otto.url_queue.append(
            ('other url', handler_mock, 'POST', {'foo': 'bar'})
        )

        response = self.get_response()
        callback = Mock()

        handle_request = otto.handle_request('some url', callback)
        handle_request(response)

        expect(otto.running_urls).to_equal(-1)
        expect(otto.url_queue).to_be_empty()
        expect(callback.called).to_be_true()
        fetch_mock.assert_called_once_with('other url', handler_mock, 'POST', foo='bar')

    def test_can_handle_wait_timeout(self):
        otto = TornadoOctopus(cache=False, auto_start=True)
        otto.ioloop = Mock()

        otto.handle_wait_timeout(1, None)

        expect(otto.ioloop.stop.called).to_be_true()

    def test_can_stop(self):
        otto = TornadoOctopus(cache=False, auto_start=True)
        otto.ioloop = Mock()

        otto.stop()

        expect(otto.ioloop.stop.called).to_be_true()

    @patch.object(logging, 'debug')
    def test_can_wait_when_no_urls(self, logging_mock):
        otto = TornadoOctopus(cache=False, auto_start=True)

        otto.wait()

        logging_mock.assert_calls('No urls to wait for. Returning immediately.')

    def test_can_wait_when_urls_and_timeout(self):
        otto = TornadoOctopus(cache=False, auto_start=True)
        otto.ioloop = Mock()
        otto.running_urls = 10

        otto.wait()

        expect(otto.ioloop.set_blocking_signal_threshold.called)

    @patch.object(logging, 'debug')
    def test_can_wait_when_urls_and_no_timeout(self, logging_mock):
        otto = TornadoOctopus(cache=False, auto_start=True)
        otto.ioloop = Mock()
        otto.running_urls = 10

        otto.wait(0)

        logging_mock.assert_calls('Waiting for urls to be retrieved.')

    def test_can_get_many_urls(self):
        urls = [
            'http://www.twitter.com',
            'http://www.cnn.com',
            'http://www.bbc.com',
            'http://www.facebook.com'
        ]
        otto = TornadoOctopus(concurrency=4, auto_start=True)

        def handle_url_response(url, response):
            self.responses[url] = response

        for url in urls:
            otto.enqueue(url, handle_url_response)

        otto.wait(2)

        expect(self.responses).to_length(4)

        for url in urls:
            expect(self.responses).to_include(url)
            expect(self.responses[url].status_code).to_equal(200)

    def test_can_handle_invalid_urls(self):
        url = 'http://kagdjdkjgka.fk'
        otto = TornadoOctopus(concurrency=1, auto_start=True)

        def handle_url_response(url, response):
            self.response = response

        otto.enqueue(url, handle_url_response)

        otto.wait(5)

        expect(self.response).not_to_be_null()
        expect(self.response.status_code).to_equal(599)
        expect(self.response.text).to_be_null()
        expect(self.response.error).not_to_be_null()

    def test_can_handle_timeouts(self):
        url = 'http://baidu.com'
        otto = TornadoOctopus(concurrency=1, request_timeout_in_seconds=0.1, auto_start=True)

        def handle_url_response(url, response):
            self.response = response

        otto.enqueue(url, handle_url_response)

        otto.wait(5)

        expect(self.response.status_code).to_equal(599)
        expect(self.response.text).to_be_null()
        expect(self.response.error).not_to_be_null()
