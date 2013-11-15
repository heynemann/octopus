#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time

from preggy import expect

from octopus import Octopus
from tests import TestCase


class TestOctopus(TestCase):
    def test_can_create_octopus(self):
        otto = Octopus(concurrency=20)
        expect(otto.concurrency).to_equal(20)
        expect(otto.auto_start).to_be_false()

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

        self.response = None

        def handle_url_response(response):
            self.response = response

        otto.enqueue('http://www.google.com', handle_url_response)
        otto.start()

        tried = 0
        while not self.response and tried < 30:
            tried += 1
            time.sleep(0.1)

        expect(self.response).not_to_be_null()
        expect(self.response.status_code).to_equal(200)
