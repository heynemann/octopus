octopus
=======

[![Build Status](https://travis-ci.org/heynemann/octopus.png?branch=master)](https://travis-ci.org/heynemann/octopus)
[![PyPi version](https://pypip.in/v/octopus-http/badge.png)](https://crate.io/packages/octopus-http/)
[![PyPi downloads](https://pypip.in/d/octopus-http/badge.png)](https://crate.io/packages/octopus-http/)
[![Coverage Status](https://coveralls.io/repos/heynemann/octopus/badge.png?branch=master)](https://coveralls.io/r/heynemann/octopus?branch=master)

`octopus` is a library to concurrently retrieve and report on the completion of http requests.

You can either use threads or the tornado IOLoop to asynchronously get them.

Installing
==========

Installing `octopus` is really easy:

    $ pip install octopus-http

The reason for the name of the package is that a package called `octopus` was already registered at the Python Package Index.

Using
=====

Using `octopus` with threads:

    from octopus import Octopus

    # this Octopus instance we'll run 4 threads,
    # automatically start listening to the queue and
    # we'll in-memory cache responses for 10 seconds.
    otto = Octopus(
        concurrency=4, auto_start=True, cache=True,
        expiration_in_seconds=10
    )

    def handle_url_response(url, response):
        # do something with response

    otto.enqueue('http://www.google.com', handle_url_response)
    otto.enqueue('http://www.facebook.com', handle_url_response)
    otto.enqueue('http://www.yahoo.com', handle_url_response)

    # this request will come from the cache
    otto.enqueue('http://www.google.com', handle_url_response)  

    otto.wait()  # waits until queue is empty or timeout is ellapsed

The analogous version with Tornado's IOLoop:

    from octopus import TornadoOctopus

    # this Octopus instance we'll run 4 concurrent requests max,
    # automatically start listening to the queue and
    # we'll in-memory cache responses for 10 seconds.
    otto = TornadoOctopus(
        concurrency=4, auto_start=True, cache=True,
        expiration_in_seconds=10
    )

    def handle_url_response(url, response):
        # do something with response

    otto.enqueue('http://www.google.com', handle_url_response)
    otto.enqueue('http://www.facebook.com', handle_url_response)
    otto.enqueue('http://www.yahoo.com', handle_url_response)

    # this request will come from the cache
    otto.enqueue('http://www.google.com', handle_url_response)  

    otto.wait()  # waits until queue is empty or timeout is ellapsed

API Reference
=============

Response Class
--------------

The `Response` class is the result of all requests made with `Octopus` or `TornadoOctopus`.

It has the following information:

* `url` - the url that started the request;
* `status_code` - the status code for the request;
* `cookies` - dictionary with request cookie values;
* `headers` - dictionary with response headers;
* `text` - the body of the response;
* `effective_url` - in the case of redirects, this url might be different than url;
* `error` - if an error has occurred this is where the error message will be;
* `request_time` - the time ellapsed between the start and the end of the request in seconds.

Octopus Class
-------------

This is the main unit of work in `octopus` if you want to use threads. To enqueue new urls you need to have an `Octopus` instance:

    from octopus import Octopus

    otto = Octopus()

The constructor for `Octopus` takes several configuration options:

* `concurrency`: number of threads to use to retrieve URLs (defaults to 10 threads);
* `auto_start`: Indicates whether threads should be started automatically (defaults to False);
* `cache`: If set to `True`, responses will be cached for the number of seconds specified in `expiration_in_seconds` (defaults to False);
* `expiration_in_seconds`: The number of seconds to keep url responses in the local cache (defaults to 30 seconds);
* `request_timeout_in_seconds`: The number of seconds that each request can take (defaults to 5 seconds).

Octopus.start()
---------------

If `auto_start` is set to `False`, this method must be called to start retrieving URLs. This is a **non-blocking** method.

Octopus.enqueue
---------------

Takes as arguments (url, handler, method="GET", **kwargs).

This is the main method in the `Octopus` class. This method is used to enqueue new URLs. The handler argument specifies the method to be called when the response is available.

The handler takes the form `handler(url, response)`. The response argument is a Octopus.Response instance.

You can specify a different method using the `method` argument (`POST`, `HEAD`, etc) and you can pass extra keyword arguments to the `requests.request` method using the keyword arguments for this method.

This is a **non-blocking** method.

Octopus.queue_size
------------------

This property returns the approximate number of URLs still in the queue (not retrieved yet).

Octopus.is_empty
----------------

This property returns if the URL queue is empty.

Octopus.wait(timeout=10)
------------------------

If you want to wait for all the URLs in the queue to finish loading, just call this method.

If you specify a `timeout` of `0`, `octopus` will wait until the queue is empty, no matter how long it takes.

This is a **blocking** method.

TornadoOctopus Class
--------------------

This is the main unit of work in `octopus` if you want to use Tornado's IOLoop. To enqueue new urls you need to have an `TornadoOctopus` instance:

    from octopus import TornadoOctopus

    otto = TornadoOctopus()

A **very important** thing that differs from the threaded version of Octopus is that you **MUST** call wait to get the responses, since Tornado IOLoop needs to be run in order to get the requests.

The constructor for `TornadoOctopus` takes several configuration options:

* `concurrency`: number of maximum async http requests to use to retrieve URLs (defaults to 10 requests);
* `auto_start`: Indicates whether the ioloop should be created automatically (defaults to False);
* `cache`: If set to `True`, responses will be cached for the number of seconds specified in `expiration_in_seconds` (defaults to False);
* `expiration_in_seconds`: The number of seconds to keep url responses in the local cache (defaults to 30 seconds);
* `request_timeout_in_seconds`: The number of seconds that each request can take (defaults to 10 seconds).
* `connect_timeout_in_seconds`: The number of seconds that each connection can take (defaults to 5 seconds).

TornadoOctopus.start()
---------------

If `auto_start` is set to `False`, this method must be called to create the IOLoop instance. This is a **non-blocking** method.

TornadoOctopus.enqueue
----------------------

Takes as arguments (url, handler, method="GET", **kwargs).

This is the main method in the `TornadoOctopus` class. This method is used to enqueue new URLs. The handler argument specifies the method to be called when the response is available.

The handler takes the form `handler(url, response)`. The response argument is a Octopus.Response instance.

You can specify a different method using the `method` argument (`POST`, `HEAD`, etc) and you can pass extra keyword arguments to the `AsyncHTTPClient.fetch` method using the keyword arguments for this method.

This is a **non-blocking** method.

TornadoOctopus.queue_size
-------------------------

This property returns the number of URLs still in the queue (not retrieved yet).

TornadoOctopus.is_empty
-----------------------

This property returns if the URL queue is empty.

TornadoOctopus.wait(timeout=10)
-------------------------------

In order for the IOLoop to handle callbacks, you **MUST** call wait. This is the method that gets the IOLoop to run.

If you specify a `timeout` of `0`, `octopus` will wait until the queue is empty, no matter how long it takes.

This is a **blocking** method.

Limiting Simultaneous Connections
=================================

A very common problem that can happen when using octopus is overwhelming the server you are going to. In order to make sure this
does not happen, Octopus allows users to specify a limiter class.

Each limiter class has to provide two methods `acquire` and `release`, both taking an URL as argument.

Octopus comes bundled with an in-memory limiter and a redis limiter (courtesy of the [retools project](https://github.com/bbangert/retools)). Using limiters is as simple as passing it to octopus constructor:

    from octopus import TornadoOctopus
    from octopus.limiter.in_memory.per_domain import Limiter

    # using in-memory limiter. Domains not specified here have no limit.
    limiter = Limiter(
        {'http://globo.com': 10},  # only 10 concurrent requests to this domain
        {'http://g1.globo.com': 20},  # only 20 concurrent requests to this domain
    )

    otto = TornadoOctopus(
        concurrency=4, auto_start=True, cache=True,
        expiration_in_seconds=10,
        limiter=limiter
    )

The available built-in limiters are:

* `octopus.limiter.in_memory.per_domain.Limiter`
* `octopus.limiter.redis.per_domain.Limiter`

Both take a list of dictionaries with the key being the beginning of the URL and value being the allowed concurrent connections.

The reason this is a list is that urls defined first take precedence. This allows users to single out a path in a domain that needs less connections than the rest of the domain, like this:

    # using in-memory limiter. Domains not specified here have no limit.
    limiter = Limiter(
        {'http://g1.globo.com/economia': 5},  # only 5 concurrent requests to urls that begin with this key
        {'http://g1.globo.com': 20},  # only 20 concurrent requests to the rest of the domain
    )

The redis limiter takes two additional keyword arguments:
 `redis` (a [redis.py](https://github.com/andymccurdy/redis-py) connection to redis)
 and `expiration_in_seconds` (the expiration for locks in the limiter).

**WARNING**: The in-memory limiter IS NOT thread-save, so if you are using Threaded Octopus, do not use this limiter.

Benchmark
=========

In order to decide whether `octopus` really was worth using, it features a benchmark test in it's codebase.

If you want to run it yourself (which is highly encouraged), just clone `octopus` repository and run this command:

    $ python benchmark/test_octopus.py 200 100

The first argument is the number of URLs to retrieve. The seconds argument means how many threads will be used by `octopus` to get the urls.

The test is pretty simple. Time how long it takes for requests to get the URLs sequentially and for `octopus` to get them concurrently.

The results for retrieving `2000` urls with `200` threads is as follows:

    =======
    RESULTS
    =======

    [requests] Retrieving 2000 urls took 2692.66 seconds meaning 0.74 urls/second.

    [octopus] Retrieving 2000 urls took 31.14 seconds meaning 64.22 urls/second.

    [octopus] Retrieving 2000 urls with local in-memory caching took 6.61 seconds
    meaning 302.50 urls/second.

    [octopus-tornado] Retrieving 2000 urls took 167.99 seconds
    meaning 11.91 urls/second.

    [octopus-tornado-pycurl] Retrieving 2000 urls took 171.40 seconds
    meaning 11.67 urls/second.

    Overall, threaded octopus was more than 86 times faster than sequential requests
    and tornado octopus was more than 15 times faster than sequential requests.
