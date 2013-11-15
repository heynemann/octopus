#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

from preggy import expect
from mock import Mock

from octopus import Octopus, TimeoutError
from tests import TestCase


class TestOctopus(TestCase):
    def setUp(self):
        self.response = None
        self.responses = {}

    def test_can_create_octopus(self):
        otto = Octopus(concurrency=20)
        expect(otto.concurrency).to_equal(20)
        expect(otto.auto_start).to_be_false()
        expect(otto.cache).to_be_false()

    def test_has_default_concurrency(self):
        otto = Octopus()
        expect(otto.concurrency).to_equal(10)

    def test_queue_is_empty(self):
        otto = Octopus()
        expect(otto.is_empty).to_be_true()

    def test_can_enqueue_url(self):
        otto = Octopus()

        otto.enqueue('http://www.google.com', None)

        expect(otto.queue_size).to_equal(1)

    def test_can_get_after_started(self):
        otto = Octopus(concurrency=1)

        def handle_url_response(url, response):
            self.response = response

        otto.enqueue('http://www.google.com', handle_url_response)
        otto.start()

        otto.wait(2)

        expect(self.response).not_to_be_null()
        expect(self.response.status_code).to_equal(200)

    def test_can_get_with_auto_start(self):
        otto = Octopus(concurrency=1, auto_start=True)

        def handle_url_response(url, response):
            self.response = response

        otto.enqueue('http://www.google.com', handle_url_response)

        otto.wait(2)

        expect(self.response).not_to_be_null()
        expect(self.response.status_code).to_equal(200)

    def test_times_out_on_wait(self):
        otto = Octopus(concurrency=1)

        def handle_url_response(url, response):
            self.response = response

        otto.enqueue('http://www.google.com', handle_url_response)

        try:
            otto.wait(0.1)
        except TimeoutError:
            err = sys.exc_info()[1]
            expect(err).to_have_an_error_message_of("")
        else:
            assert False, "Should not have gotten this far"

    def test_can_handle_more_urls_concurrently(self):
        urls = [
            'http://www.google.com',
            'http://www.globo.com',
            'http://www.cnn.com',
            'http://www.bbc.com'
        ]
        otto = Octopus(concurrency=4)

        def handle_url_response(url, response):
            self.responses[url] = response

        for url in urls:
            otto.enqueue(url, handle_url_response)

        otto.start()

        otto.wait(10)

        expect(self.responses).to_length(4)

        for url in urls:
            expect(self.responses).to_include(url)
            expect(self.responses[url].status_code).to_equal(200)

    def test_can_handle_cached_responses(self):
        response = Mock(status_code=200, body="whatever")

        url = 'http://www.google.com'
        otto = Octopus(concurrency=1, cache=True)
        otto.response_cache.put(url, response)

        def handle_url_response(url, response):
            self.response = response

        otto.enqueue(url, handle_url_response)

        expect(self.response).not_to_be_null()
        expect(self.response.status_code).to_equal(200)
        expect(self.response.body).to_equal("whatever")

    def test_can_handle_cached_responses_when_not_cached(self):
        url = 'http://www.google.com'
        otto = Octopus(concurrency=1, cache=True)

        def handle_url_response(url, response):
            self.response = response

        otto.enqueue(url, handle_url_response)

        otto.start()

        otto.wait(2)

        expect(self.response).not_to_be_null()
        expect(self.response.status_code).to_equal(200)
