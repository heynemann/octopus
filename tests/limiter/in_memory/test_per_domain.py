#!/usr/bin/env python
# -*- coding: utf-8 -*-

from preggy import expect

from octopus.limiter.in_memory.per_domain import Limiter as PerDomainInMemoryLimiter
from tests import TestCase


class TestPerDomain(TestCase):
    def setUp(self):
        super(TestPerDomain, self).setUp()
        self.limiter = PerDomainInMemoryLimiter(
            {'http://g1.globo.com': 10},
            {'http://globoesporte.globo.com': 10}
        )

    def test_can_create_limiter(self):
        expect(self.limiter.domains[0]).to_include('http://g1.globo.com')
        expect(self.limiter.domains).not_to_be_null()
        expect(self.limiter.domains[0]['http://g1.globo.com']).to_equal(10)

    def test_can_acquire_limit(self):
        expect(self.limiter.acquire('http://g1.globo.com')).to_be_true()
        expect(self.limiter.domain_count).to_include('http://g1.globo.com')
        expect(self.limiter.domain_count['http://g1.globo.com']).to_equal(1)

    def test_acquiring_internal_url_gets_proper_domain(self):
        expect(self.limiter.acquire('http://g1.globo.com/economia/')).to_be_true()
        expect(self.limiter.domain_count).to_include('http://g1.globo.com')
        expect(self.limiter.domain_count['http://g1.globo.com']).to_equal(1)

    def test_can_acquire_from_unknown_domain_url(self):
        limiter = PerDomainInMemoryLimiter(
            {'http://globoesporte.globo.com': 10}
        )

        expect(limiter.acquire('http://g1.globo.com/economia/')).to_be_true()
        expect(limiter.domain_count).to_be_empty()

    def test_can_release(self):
        url = 'http://g1.globo.com/economia/'
        self.limiter.acquire(url)
        self.limiter.release(url)

        expect(self.limiter.domain_count['http://g1.globo.com']).to_equal(0)

    def test_can_get_domain_from_url(self):
        expect(self.limiter.get_domain_from_url('http://g1.globo.com/economia/')).to_equal('http://g1.globo.com')

    def test_can_get_domain_limit(self):
        url = 'http://g1.globo.com/economia/'
        expect(self.limiter.get_domain_limit(url)).to_equal(10)

        self.limiter.acquire(url)
        expect(self.limiter.get_domain_limit(url)).to_equal(10)

        expect(self.limiter.get_domain_limit('http://www.google.com')).to_equal(0)
