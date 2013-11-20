#!/usr/bin/env python
# -*- coding: utf-8 -*-

from threading import Thread
import time

from tornado.ioloop import IOLoop
from tornado.httpclient import AsyncHTTPClient, HTTPRequest
try:
    import pycurl  # NOQA
    PYCURL_AVAILABLE = True
except ImportError:
    PYCURL_AVAILABLE = False

from octopus.cache import Cache
from octopus.model import Response


class TornadoOctopus(object):
    def __init__(
            self, concurrency=10, auto_start=False, cache=False,
            expiration_in_seconds=30, request_timeout_in_seconds=10,
            connect_timeout_in_seconds=5, ignore_pycurl=False):

        self.concurrency = concurrency
        self.auto_start = auto_start

        self.cache = cache
        self.response_cache = Cache(expiration_in_seconds=expiration_in_seconds)
        self.request_timeout_in_seconds = request_timeout_in_seconds
        self.connect_timeout_in_seconds = connect_timeout_in_seconds

        self.ignore_pycurl = ignore_pycurl

        self.running_urls = 0
        self.url_queue = []

        if PYCURL_AVAILABLE and not self.ignore_pycurl:
            AsyncHTTPClient.configure("tornado.curl_httpclient.CurlAsyncHTTPClient")
        #else:
            #logging.warn(
                #'pycurl is not enabled and performance will suffer badly, '
                #'as well as being less reliable. Please consider installing '
                #'the latest versions of libcurl an pycurl.'
            #)

        if auto_start:
            self.start()

    def start(self):
        self.ioloop = IOLoop()
        self.http_client = AsyncHTTPClient(io_loop=self.ioloop)

        t = Thread(target=self.start_ioloop, args=(self.ioloop, ))
        t.daemon = True
        t.start()

    def start_ioloop(self, ioloop):
        ioloop.start()

    def from_tornado_response(self, url, response):
        cookies = response.request.headers.get('Cookie', '')
        if cookies:
            cookies = dict([cookie.split('=') for cookie in cookies.split(';')])

        return Response(
            url=url, status_code=response.code,
            headers=dict([(key, value) for key, value in response.headers.items()]),
            cookies=cookies,
            text=response.body, effective_url=response.effective_url,
            error=response.error and str(response.error) or None,
            request_time=response.request_time
        )

    def handle_request(self, url, callback):
        def handle(response):
            response = self.from_tornado_response(url, response)

            if self.cache:
                self.response_cache.put(url, response)

            self.running_urls -= 1
            callback(url, response)

            if self.running_urls < self.concurrency and self.url_queue:
                request_url, handler, method, kw = self.url_queue.pop()
                self.fetch(request_url, handler, method, **kw)

            #if not self.url_queue:
                #self.ioloop.stop()

        return handle

    def enqueue(self, url, handler, method='GET', **kw):
        if self.cache:
            response = self.response_cache.get(url)

            if response is not None:
                handler(url, response)
                return

        if self.running_urls < self.concurrency:
            self.fetch(url, handler, method, **kw)
        else:
            self.url_queue.append((url, handler, method, kw))

    def fetch(self, url, handler, method, **kw):
        self.running_urls += 1

        request = HTTPRequest(
            url=url,
            method=method,
            connect_timeout=self.connect_timeout_in_seconds,
            request_timeout=self.request_timeout_in_seconds,
            **kw
        )

        self.http_client.fetch(request, self.handle_request(url, handler))

    def wait(self, timeout=10):
        started = time.time()

        if timeout > 0:
            while (len(self.url_queue) > 0 or self.running_urls > 0) and (time.time() - started) < timeout:
                time.sleep(0.1)
        else:
            while len(self.url_queue) > 0 or self.running_urls > 0:
                time.sleep(0.1)

        self.ioloop.stop()
