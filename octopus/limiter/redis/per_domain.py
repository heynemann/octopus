#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

from retools.limiter import Limiter as ReToolsLimiter

from octopus.limiter.in_memory.per_domain import Limiter as InMemoryPerDomainLimiter


class Limiter(InMemoryPerDomainLimiter):
    def __init__(self, *domains, **kw):
        super(InMemoryPerDomainLimiter, self).__init__()  # Skips InMemoryPerDomainLimiter constructor

        if not 'redis' in kw:
            raise RuntimeError('You must specify a connection to redis in order to use Redis Limiter.')

        self.redis = kw['redis']
        self.expiration_in_seconds = float(kw.get('expiration_in_seconds', 10))
        self.domains = domains
        self.limiters = {}

        for domain in self.domains:
            for key, limit in domain.items():
                self.limiters[key] = ReToolsLimiter(
                    limit=limit,
                    prefix='limit-for-%s' % key,
                    expiration_in_seconds=self.expiration_in_seconds,
                    redis=self.redis
                )

    def acquire(self, url):
        domain = self.get_domain_from_url(url)
        if domain is None:
            logging.info('Tried to acquire lock to a domain that was not specified in the limiter (%s).' % url)
            return True

        could_lock = self.limiters[domain].acquire_limit(url)

        if not could_lock:
            self.publish_lock_miss(url)

        return could_lock

    def release(self, url):
        domain = self.get_domain_from_url(url)

        if domain is None:
            logging.info('Tried to release lock to a domain that was not specified in the limiter (%s).' % url)
            return True

        self.limiters[domain].release_limit(url)
