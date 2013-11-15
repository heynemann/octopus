#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time

from preggy import expect

from octopus.cache import Cache
from tests import TestCase


class TestCache(TestCase):
    def test_can_create_cache(self):
        cache = Cache(expiration_in_seconds=45)
        expect(cache.expiration_in_seconds).to_equal(45)
        expect(cache.responses).to_be_empty()

    def test_get_returns_none_if_not_put(self):
        cache = Cache(expiration_in_seconds=45)

        expect(cache.get('http://www.google.com')).to_be_null()

    def test_get_returns_none_if_expired(self):
        cache = Cache(expiration_in_seconds=0.1)

        cache.put('http://www.google.com', 'response')

        time.sleep(0.5)

        expect(cache.get('http://www.google.com')).to_be_null()

        expect(cache.responses).not_to_include('http://www.google.com')

    def test_can_get_after_put(self):
        cache = Cache(expiration_in_seconds=10)
        cache.put('http://www.google.com', 'response')
        expect(cache.get('http://www.google.com')).to_equal('response')
