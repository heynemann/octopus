#!/usr/bin/env python
# -*- coding: utf-8 -*-


from datetime import datetime, timedelta


class Cache(object):
    def __init__(self, expiration_in_seconds):
        self.responses = {}
        self.expiration_in_seconds = expiration_in_seconds

    def put(self, url, response):
        self.responses[url] = {
            'response': response,
            'expires': datetime.now() + timedelta(seconds=self.expiration_in_seconds)
        }

    def get(self, url):
        if url not in self.responses:
            return None

        data = self.responses[url]

        if data['expires'] <= datetime.now():
            del self.responses[url]
            return None

        return data['response']
