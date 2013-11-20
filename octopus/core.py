#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from time import time
from datetime import timedelta
from threading import Thread

try:
    import requests
    import requests.exceptions
except ImportError:
    print("Can't import requests. Probably setup.py installing package.")

from octopus.cache import Cache
from octopus.model import Response

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


class ResponseError(object):
    def __init__(self, url, status_code, text, error=None, elapsed=None):
        self.url = url
        self.status_code = status_code
        self.text = text
        self.error = error
        self.headers = {}
        self.cookies = {}
        self.effective_url = url
        self.elapsed = elapsed

    def close(self):
        pass


class Octopus(object):
    def __init__(self, concurrency=10, auto_start=False, cache=False, expiration_in_seconds=30, request_timeout_in_seconds=5):
        self.concurrency = concurrency
        self.auto_start = auto_start

        self.cache = cache
        self.response_cache = Cache(expiration_in_seconds=expiration_in_seconds)
        self.request_timeout_in_seconds = request_timeout_in_seconds

        self.url_queue = OctopusQueue()

        if auto_start:
            self.start()

    def from_requests_response(self, url, response):
        return Response(
            url=url, status_code=response.status_code,
            headers=dict([(key, value) for key, value in response.headers.items()]),
            cookies=dict([(key, value) for key, value in response.cookies.items()]),
            text=response.text, effective_url=response.url,
            error=response.status_code > 399 and response.text or None,
            request_time=response.elapsed and response.elapsed.total_seconds or 0
        )

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
                try:
                    response = requests.request(method, url, timeout=self.request_timeout_in_seconds, **kwargs)
                except requests.ConnectionError:
                    err = sys.exc_info()[1]
                    response = ResponseError(
                        url=url,
                        status_code=500,
                        text=str(err),
                        error=err
                    )
                except requests.exceptions.Timeout:
                    err = sys.exc_info()[1]
                    response = ResponseError(
                        url=url,
                        status_code=500,
                        text=str(err),
                        error=err,
                        elapsed=timedelta(seconds=self.request_timeout_in_seconds)
                    )
                except Exception:
                    err = sys.exc_info()[1]
                    response = ResponseError(
                        url=url,
                        status_code=599,
                        text=str(err),
                        error=err
                    )

                original_response = response

                response = self.from_requests_response(url, response)

                original_response.close()

                if self.cache:
                    self.response_cache.put(url, response)

            handler(url, response)

            self.url_queue.task_done()

    def wait(self, timeout=10):
        if timeout > 0:
            self.url_queue.join_with_timeout(timeout=timeout)
        else:
            self.url_queue.join()
