#!/usr/bin/env python
# -*- coding: utf-8 -*-

from preggy import expect

from octopus import Octopus
from tests import TestCase


class TestOctopus(TestCase):
    def test_can_create_octopus(self):
        otto = Octopus(concurrency=20)
        expect(otto.concurrency).to_equal(20)

    def test_has_default_concurrency(self):
        otto = Octopus()
        expect(otto.concurrency).to_equal(10)

    def test_can_enqueue_url(self):
        otto = Octopus()

        otto.enqueue('http://www.google.com')

        expect(otto.queue_size).to_equal(1)
