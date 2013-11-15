#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from random import choice
from time import time

import requests

from octopus import Octopus


def main(repetitions, concurrency):

    # alexa top sites
    urls = [
        'http://google.com',
        'http://facebook.com',
        'http://youtube.com',
        'http://yahoo.com',
        'http://wikipedia.org',
        'http://linkedin.com',
        'http://live.com',
        'http://twitter.com',
        'http://amazon.com',
        'http://blogspot.com',
        'http://wordpress.com',
        'http://bing.com',
        'http://ebay.com',
        'http://google.de',
        'http://tumblr.com',
    ]

    urls_to_retrieve = [choice(urls) for i in range(repetitions)]

    message = "Retrieving URLs sequentially with Requests..."
    print
    print("=" * len(message))
    print(message)
    print("=" * len(message))
    print

    start_time = time()

    for url_index, url in enumerate(urls_to_retrieve):
        print "%.2f%% - getting %s..." % (
            float(url_index) / float(repetitions) * 100,
            url
        )
        assert requests.get(url).status_code == 200

    requests_total_time = time() - start_time

    message = "Retrieving URLs concurrently with Octopus..."
    print
    print("=" * len(message))
    print(message)
    print("=" * len(message))
    print

    otto = Octopus(concurrency=concurrency)

    for url in urls_to_retrieve:
        otto.enqueue(url, handle_url_response)

    start_time = time()
    otto.start()
    otto.wait()

    otto_total_time = time() - start_time

    message = "Retrieving URLs concurrently with Octopus with caching enabled..."
    print
    print("=" * len(message))
    print(message)
    print("=" * len(message))
    print

    otto = Octopus(concurrency=concurrency, cache=True, auto_start=True)

    for url in urls_to_retrieve:
        otto.enqueue(url, handle_url_response)

    start_time = time()
    otto.wait()

    otto_cached_total_time = time() - start_time

    message = "RESULTS"
    print
    print("=" * len(message))
    print(message)
    print("=" * len(message))
    print

    print "[requests] Retrieving %d urls took %.2f seconds meaning %.2f urls/second" % (
        repetitions,
        requests_total_time,
        repetitions / requests_total_time
    )
    print

    print "[octopus] Retrieving %d urls took %.2f seconds meaning %.2f urls/second" % (
        repetitions,
        otto_total_time,
        repetitions / otto_total_time
    )
    print

    print "[octopus] Retrieving %d urls with local in-memory caching took %.2f seconds meaning %.2f urls/second" % (
        repetitions,
        otto_total_time,
        repetitions / otto_total_time
    )
    print

    print "Overall, octopus was more than %.2f times faster than sequential requests." % (
        int(requests_total_time / otto_total_time)
    )

    print


def handle_url_response(url, response):
    print "Got %s!" % url
    assert response.status_code == 200, "Expected status code for %s to be 200, got %s" % (url, response.status_code)


if __name__ == '__main__':
    main(int(sys.argv[1]), int(sys.argv[2]))
