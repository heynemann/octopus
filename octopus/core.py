#!/usr/bin/env python
# -*- coding: utf-8 -*-

from time import time
from threading import Thread

try:
    import requests
except ImportError:
    print("Can't import requests. Probably setup.py installing package.")

from octopus.cache import Cache

try:

    from six.moves import queue

    class OctopusQueue(queue.Queue):
        # from http://stackoverflow.com/questions/1564501/add-timeout-argument-to-pythons-queue-join
        def join_with_timeout(self, timeout):
            self.all_tasks_done.acquire()
            try:
                endtime = time() + timeout
                while self.unfinished_tasks:
                    remaining = endtime - time()
                    if remaining <= 0.0:
                        raise TimeoutError
                    self.all_tasks_done.wait(remaining)
            finally:
                self.all_tasks_done.release()

except ImportError:
    print("Can't import six. Probably setup.py installing package.")


class TimeoutError(RuntimeError):
    pass


class Octopus(object):
    def __init__(self, concurrency=10, auto_start=False, cache=False, expiration_in_seconds=30):
        self.concurrency = concurrency
        self.auto_start = auto_start

        self.cache = cache
        self.response_cache = Cache(expiration_in_seconds=expiration_in_seconds)

        self.url_queue = OctopusQueue()

        if auto_start:
            self.start()

    def enqueue(self, url, handler, method='GET', **kw):
        if self.cache:
            response = self.response_cache.get(url)
            if response is not None:
                handler(url, response)
                return

        self.url_queue.put_nowait((url, handler, method, kw))

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
            url, handler, method, kwargs = self.url_queue.get()

            response = None
            if self.cache:
                response = self.response_cache.get(url)

            if response is None:
                response = requests.request(method, url, **kwargs)

                if self.cache:
                    self.response_cache.put(url, response)

            handler(url, response)

            self.url_queue.task_done()

    def wait(self, timeout=10):
        if timeout > 0:
            self.url_queue.join_with_timeout(timeout=timeout)
        else:
            self.url_queue.join()
