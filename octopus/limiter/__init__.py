#!/usr/bin/env python
# -*- coding: utf-8 -*-

from cyrusbus import Bus


class Limiter(object):
    def __init__(self, limiter_miss_timeout_ms=None):
        self.bus = Bus()
        self.limiter_miss_timeout_ms = limiter_miss_timeout_ms
        if self.limiter_miss_timeout_ms is None:
            self.limiter_miss_timeout_ms = 500

    def handle_callbacks(self, callback):
        def handle(bus, *args, **kw):
            callback(*args, **kw)
        return handle

    def subscribe_to_lock_miss(self, callback):
        self.bus.subscribe('limiter.miss', self.handle_callbacks(callback))

    def publish_lock_miss(self, url):
        self.bus.publish('limiter.miss', url)
