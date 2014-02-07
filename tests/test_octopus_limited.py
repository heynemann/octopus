#!/usr/bin/env python
# -*- coding: utf-8 -*-

from preggy import expect

from octopus import Octopus
from octopus.limiter.redis.per_domain import Limiter as PerDomainRedisLimiter
from tests import TestCase


class TestThreadedOctopusAgainstLimiter(TestCase):
    def setUp(self):
        super(TestThreadedOctopusAgainstLimiter, self).setUp()

        self.response = None
        self.url = None
        self.responses = {}

    def handle_url_response(self, url, response):
        self.responses[url] = response

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

        otto.wait(2)

        expect(self.responses).to_length(4)
        expect(self.redis.zcard('limit-for-http://g1.globo.com')).to_equal(0)
        expect(self.redis.zcard('limit-for-http://globoesporte.globo.com')).to_equal(0)
