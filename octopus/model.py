#!/usr/bin/env python
# -*- coding: utf-8 -*-


class Response(object):
    def __init__(
        self, url, status_code,
        headers, cookies, text, effective_url,
        error, request_time
    ):
        self.url = url
        self.status_code = status_code
        self.cookies = cookies
        self.headers = headers
        self.text = text
        self.effective_url = effective_url
        self.error = error
        self.request_time = request_time
