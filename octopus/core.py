#!/usr/bin/env python
# -*- coding: utf-8 -*-

from collections import defaultdict
from threading import Thread

import requests
from six.moves import queue


class Octopus(object):
    def __init__(self, concurrency=10, auto_start=False):
        self.concurrency = concurrency
        self.auto_start = auto_start

        self.url_queue = queue.Queue()

    def enqueue(self, url, handler):
        self.url_queue.put_nowait((url, handler))

    @property
    def queue_size(self):
        return self.url_queue.qsize()

    @property
    def is_empty(self):
        return self.url_queue.empty()

    def start(self):
        for i in range(self.concurrency):
            t = Thread(target=self.do_work)
            t.daemon = True
            t.start()

    def do_work(self):
        while True:
            url, handler = self.url_queue.get()

            response = requests.get(url)
            handler(response)

            self.url_queue.task_done()
