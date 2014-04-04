#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from datetime import timedelta

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
            connect_timeout_in_seconds=5, ignore_pycurl=False,
            limiter=None, allow_connection_reuse=True):

        self.concurrency = concurrency
        self.auto_start = auto_start
        self.last_timeout = None

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
            self.allow_connection_reuse = allow_connection_reuse
        else:
            self.allow_connection_reuse = True

        if auto_start:
            logging.debug('Auto starting...')
            self.start()

        self.limiter = limiter

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
            self.get_next_url(url, handler, method, **kw)
        else:
            logging.debug('Queue is full. Enqueueing %s for future fetch.' % url)
            self.url_queue.append((url, handler, method, kw))

    def fetch(self, url, handler, method, **kw):
        self.running_urls += 1

        if self.cache:
            response = self.response_cache.get(url)

            if response is not None:
                logging.debug('Cache hit on %s.' % url)
                self.running_urls -= 1
                handler(url, response)
                return

        logging.info('Fetching %s...' % url)

        request = HTTPRequest(
            url=url,
            method=method,
            connect_timeout=self.connect_timeout_in_seconds,
            request_timeout=self.request_timeout_in_seconds,
            prepare_curl_callback=self.handle_curl_callback,
            **kw
        )

        self.http_client.fetch(request, self.handle_request(url, handler))

    def handle_curl_callback(self, curl):
        if not self.allow_connection_reuse:
            curl.setopt(pycurl.FRESH_CONNECT, 1)

    def get_next_url(self, request_url=None, handler=None, method=None, **kw):
        if request_url is None:
            if not self.url_queue:
                return

            request_url, handler, method, kw = self.url_queue.pop()

        self.fetch_next_url(request_url, handler, method, **kw)

    def fetch_next_url(self, request_url, handler, method, **kw):
        if self.limiter and not self.limiter.acquire(request_url):
            logging.info('Could not acquire limit for url "%s".' % request_url)

            self.url_queue.append((request_url, handler, method, kw))
            deadline = timedelta(seconds=self.limiter.limiter_miss_timeout_ms / 1000.0)
            self.ioloop.add_timeout(deadline, self.get_next_url)
            self.limiter.publish_lock_miss(request_url)
            return False

        logging.debug('Queue has space available for fetching %s.' % request_url)
        self.fetch(request_url, handler, method, **kw)
        return True

    def handle_request(self, url, callback):
        def handle(response):
            logging.debug('Handler called for url %s...' % url)
            self.running_urls -= 1

            response = self.from_tornado_response(url, response)
            logging.info('Got response(%s) from %s.' % (response.status_code, url))

            if self.cache and response and response.status_code < 399:
                logging.debug('Putting %s into cache.' % url)
                self.response_cache.put(url, response)

            if self.limiter:
                self.limiter.release(url)

            try:
                callback(url, response)
            except Exception:
                logging.exception('Error calling callback for %s.' % url)

            if self.running_urls < self.concurrency and self.url_queue:
                self.get_next_url()

            logging.debug('Getting %d urls and still have %d more urls to get...' % (self.running_urls, self.remaining_requests))
            if self.running_urls < 1 and self.remaining_requests == 0:
                logging.debug('Nothing else to get. Stopping Octopus...')
                self.stop()

        return handle

    def handle_wait_timeout(self, signal_number, frames):
        logging.debug('Timeout waiting for IOLoop to finish. Stopping IOLoop manually.')
        self.stop(force=True)

    def wait(self, timeout=10):
        self.last_timeout = timeout
        if not self.url_queue and not self.running_urls:
            logging.debug('No urls to wait for. Returning immediately.')
            return

        if timeout:
            logging.debug('Waiting for urls to be retrieved for %s seconds.' % timeout)
            self.ioloop.set_blocking_signal_threshold(timeout, self.handle_wait_timeout)
        else:
            logging.debug('Waiting for urls to be retrieved.')

        logging.info('Starting IOLoop with %d URLs still left to process.' % self.remaining_requests)
        self.ioloop.start()

    @property
    def remaining_requests(self):
        return len(self.url_queue)

    def stop(self, force=False):
        logging.info('Stopping IOLoop with %d URLs still left to process.' % self.remaining_requests)
        self.ioloop.stop()
