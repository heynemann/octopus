octopus
=======

[![Build Status](https://travis-ci.org/heynemann/octopus.png?branch=master)](https://travis-ci.org/heynemann/octopus)
[![PyPi version](https://pypip.in/v/octopus-http/badge.png)](https://crate.io/packages/octopus-http/)
[![PyPi downloads](https://pypip.in/d/octopus-http/badge.png)](https://crate.io/packages/octopus-http/)
[![Coverage Status](https://coveralls.io/repos/heynemann/octopus/badge.png?branch=master)](https://coveralls.io/r/heynemann/octopus?branch=master)

octopus is a library to use threads to concurrently retrieve and report on the completion of http requests

Installing
==========

Installing octopus is really easy:

    $ pip install octopus-http

The reason for the name of the package is that a package called `octopus` was already registered at the Python Package Index.

Using
=====

Using octopus is pretty simple:

    # this Octopus instance we'll run 4 threads,
    # automatically start listening to the queue and
    # we'll in-memory cache responses for 10 seconds.
    otto = Octopus(concurrency=4, auto_start=True, cache=True, expiration_in_seconds=10)

    def handle_url_response(url, response):
        # do something with response

    otto.enqueue('http://www.google.com', handle_url_response)
    otto.enqueue('http://www.facebook.com', handle_url_response)
    otto.enqueue('http://www.yahoo.com', handle_url_response)
    otto.enqueue('http://www.google.com', handle_url_response)  # will come from the cache

    otto.wait()  # waits until queue is empty or timeout is ellapsed

Benchmark
=========

In order to decide whether Octopus really was worth using, it features a benchmark test in it's codebase.

If you want to run it yourself (which is highly encouraged), just clone Octopus codebase and run this command:

    $ python benchmark/test_octopus 200 100

The first argument is the number of URLs to retrieve. The seconds argument means how many threads will be used by octopus to get the urls.

The test is pretty simple. Time how long it takes for requests to get the URLs sequentially and for octopus to get them concurrently.

The results for retrieving 1000 urls with 200 threads is as follows:

  =======
  RESULTS
  =======

  [requests] Retrieving 200 urls took 263.26 seconds meaning 0.76 urls/second

  [octopus] Retrieving 200 urls took 12.87 seconds meaning 15.54 urls/second

  Overall, octopus was more than 20.00 times faster than sequential requests.
