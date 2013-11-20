#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

try:
    from tornado.ioloop import IOLoop
    from tornado.httpclient import AsyncHTTPClient, HTTPRequest
except ImportError:
    print("Can't import tornado. Probably setup.py installing package.")

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
            logging.debug('pycurl is available, thus Octopus will be using it instead of tornado\'s simple http client.')
            AsyncHTTPClient.configure("tornado.curl_httpclient.CurlAsyncHTTPClient")

        if auto_start:
            logging.debug('Auto starting...')
            self.start()

    @property
    def queue_size(self):
        return len(self.url_queue)

    @property
    def is_empty(self):
        return self.queue_size == 0

    def start(self):
        logging.debug('Creating IOLoop and http_client.')
        self.ioloop = IOLoop()
        self.http_client = AsyncHTTPClient(io_loop=self.ioloop)

    @classmethod
    def from_tornado_response(cls, url, response):
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

    def enqueue(self, url, handler, method='GET', **kw):
        logging.debug('Enqueueing %s...' % url)

        if self.cache:
            response = self.response_cache.get(url)

            if response is not None:
                logging.debug('Cache hit on %s.' % url)
                handler(url, response)
                return

        if self.running_urls < self.concurrency:
            logging.debug('Queue has space available for fetching %s.' % url)
            self.fetch(url, handler, method, **kw)
        else:
            logging.debug('Queue is full. Enqueueing %s for future fetch.' % url)
            self.url_queue.append((url, handler, method, kw))

    def fetch(self, url, handler, method, **kw):
        self.running_urls += 1

        if self.cache:
            response = self.response_cache.get(url)

            if response is not None:
                logging.debug('Cache hit on %s.' % url)
                handler(url, response)
                return

        logging.info('Fetching %s...' % url)

        request = HTTPRequest(
            url=url,
            method=method,
            connect_timeout=self.connect_timeout_in_seconds,
            request_timeout=self.request_timeout_in_seconds,
            **kw
        )

        self.http_client.fetch(request, self.handle_request(url, handler))

    def handle_request(self, url, callback):
        def handle(response):
            response = self.from_tornado_response(url, response)
            logging.info('Got response(%s) from %s.' % (response.status_code, url))

            if self.cache:
                logging.debug('Putting %s into cache.' % url)
                self.response_cache.put(url, response)

            self.running_urls -= 1
            callback(url, response)

            if self.running_urls < self.concurrency and self.url_queue:
                request_url, handler, method, kw = self.url_queue.pop()
                logging.debug('Queue has space available for fetching %s.' % request_url)
                self.fetch(request_url, handler, method, **kw)

            if self.running_urls < 1:
                logging.debug('Nothing else to get. Stopping Octopus...')
                self.stop()

        return handle

    def handle_wait_timeout(self, signal_number, frames):
        logging.debug('Timeout waiting for IOLoop to finish. Stopping IOLoop manually.')
        self.ioloop.stop()

    def wait(self, timeout=10):
        if not self.url_queue and not self.running_urls:
            logging.debug('No urls to wait for. Returning immediately.')
            return

        if timeout:
            logging.debug('Waiting for urls to be retrieved for %s seconds.' % timeout)
            self.ioloop.set_blocking_signal_threshold(timeout, self.handle_wait_timeout)
        else:
            logging.debug('Waiting for urls to be retrieved.')

        self.ioloop.start()

    def stop(self):
        logging.debug('Stopping IOLoop...')
        self.ioloop.stop()
