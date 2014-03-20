#!/usr/bin/env python
# -*- coding: utf-8 -*-

from preggy import expect

from octopus.limiter import Limiter
from tests import TestCase


class TestBaseLimiter(TestCase):
    def setUp(self):
        super(TestBaseLimiter, self).setUp()
        self.limiter = Limiter()
        self.handled_url = None

    def test_has_bus(self):
        expect(self.limiter.bus).not_to_be_null()

    def test_can_subscribe(self):
        def handle_lock_miss(url):
            pass

        self.limiter.subscribe_to_lock_miss(handle_lock_miss)

        expect(self.limiter.bus.has_any_subscriptions('limiter.miss')).to_be_true()

    def test_can_get_lock_miss(self):
        def handle_lock_miss(url):
            self.handled_url = url

        self.limiter.subscribe_to_lock_miss(handle_lock_miss)

        self.limiter.publish_lock_miss('some-url')

        expect(self.handled_url).to_equal('some-url')
