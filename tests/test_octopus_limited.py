#!/usr/bin/env python
# -*- coding: utf-8 -*-

from preggy import expect

from octopus import Octopus
from octopus.limiter.redis.per_domain import Limiter as PerDomainRedisLimiter
from octopus.limiter.in_memory.per_domain import Limiter as PerDomainInMemoryLimiter
from tests import TestCase


class TestThreadedOctopusAgainstLimiter(TestCase):
    def setUp(self):
        super(TestThreadedOctopusAgainstLimiter, self).setUp()

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
        limiter = PerDomainRedisLimiter(
            {'http://g1.globo.com': 1},
            {'http://globoesporte.globo.com': 1},
            redis=self.redis
        )
        otto = Octopus(concurrency=10, auto_start=True, limiter=limiter)

        otto.enqueue('http://globoesporte.globo.com', self.handle_url_response)
        otto.enqueue('http://globoesporte.globo.com/futebol/times/flamengo/', self.handle_url_response)
        otto.enqueue('http://g1.globo.com', self.handle_url_response)
        otto.enqueue('http://g1.globo.com/economia', self.handle_url_response)

        otto.wait(10)

        expect(self.responses).to_length(4)
        expect(self.redis.zcard('limit-for-http://g1.globo.com')).to_equal(0)
        expect(self.redis.zcard('limit-for-http://globoesporte.globo.com')).to_equal(0)

    def test_should_call_limiter_miss_twice(self):
        limiter = PerDomainInMemoryLimiter(
            {'http://g1.globo.com': 1},
            {'http://globoesporte.globo.com': 1},
        )
        limiter.subscribe_to_lock_miss(self.handle_limiter_miss)
        otto = Octopus(concurrency=10, auto_start=True, limiter=limiter)

        otto.enqueue('http://globoesporte.globo.com/', self.handle_url_response)
        otto.enqueue('http://globoesporte.globo.com/futebol/times/flamengo/', self.handle_url_response)
        otto.enqueue('http://g1.globo.com/', self.handle_url_response)
        otto.enqueue('http://g1.globo.com/economia/', self.handle_url_response)

        otto.wait()

        expect(self.cache_miss).to_length(2)
