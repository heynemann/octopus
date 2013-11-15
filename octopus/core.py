#!/usr/bin/env python
# -*- coding: utf-8 -*-


from six.moves import queue


class Octopus(object):
    def __init__(self, concurrency=10):
        self.concurrency = concurrency

        self.url_queue = queue.Queue()

    def enqueue(self, url):
        self.url_queue.put_nowait(url)

    @property
    def queue_size(self):
        return self.url_queue.qsize()
