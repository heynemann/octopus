#!/usr/bin/env python
# -*- coding: utf-8 -*-

from preggy import expect

from octopus import TornadoOctopus
from octopus.limiter.in_memory.per_domain import Limiter as PerDomainInMemoryLimiter
from tests import TestCase


class TestInMemoryLimiter(TestCase):
    def setUp(self):
        self.response = None
        self.url = None
        self.responses = {}

    def handle_url_response(self, url, response):
        self.responses[url] = response

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
        expect(limiter.domain_count.keys()).to_be_like(['http://g1.globo.com', 'http://globoesporte.globo.com'])
