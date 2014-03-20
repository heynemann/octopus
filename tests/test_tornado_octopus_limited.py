#!/usr/bin/env python
# -*- coding: utf-8 -*-

from preggy import expect

from octopus import TornadoOctopus
from octopus.limiter.redis.per_domain import Limiter as PerDomainRedisLimiter
from octopus.limiter.in_memory.per_domain import Limiter as PerDomainInMemoryLimiter
from tests import TestCase


class TestTornadoCoreLimited(TestCase):
    def setUp(self):
        super(TestTornadoCoreLimited, self).setUp()

        self.response = None
        self.url = None
        self.responses = {}
        self.cache_miss = set()
        self.redis.flushall()

    def handle_url_response(self, url, response):
        self.responses[url] = response

    def handle_limiter_miss(self, url):
        self.cache_miss.add(url)

    def test_should_not_get_more_than_one_url_for_same_domain_concurrently(self):
        limiter = PerDomainInMemoryLimiter(
            {'http://g1.globo.com': 1},
            {'http://globoesporte.globo.com': 1}
        )
        otto = TornadoOctopus(concurrency=10, auto_start=True, limiter=limiter)

        otto.enqueue('http://globoesporte.globo.com', self.handle_url_response)
        otto.enqueue('http://globoesporte.globo.com/futebol/times/flamengo/', self.handle_url_response)
        otto.enqueue('http://g1.globo.com', self.handle_url_response)
        otto.enqueue('http://g1.globo.com/economia', self.handle_url_response)

        otto.wait(2)

        expect(self.responses).to_length(4)
        expect(list(limiter.domain_count.keys())).to_be_like(['http://g1.globo.com', 'http://globoesporte.globo.com'])

    def test_should_call_limiter_miss_twice(self):
        limiter = PerDomainRedisLimiter(
            {'http://g1.globo.com': 1},
            {'http://globoesporte.globo.com': 1},
            redis=self.redis
        )
        limiter.subscribe_to_lock_miss(self.handle_limiter_miss)
        otto = TornadoOctopus(concurrency=10, auto_start=True, limiter=limiter)

        otto.enqueue('http://globoesporte.globo.com/', self.handle_url_response)
        otto.enqueue('http://globoesporte.globo.com/futebol/times/flamengo/', self.handle_url_response)
        otto.enqueue('http://g1.globo.com/', self.handle_url_response)
        otto.enqueue('http://g1.globo.com/economia/', self.handle_url_response)

        otto.wait()

        expect(self.cache_miss).to_length(2)
