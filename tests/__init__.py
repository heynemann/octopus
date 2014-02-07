#!/usr/bin/env python
# -*- coding: utf-8 -*-

from unittest import TestCase as PythonTestCase

import redis


class TestCase(PythonTestCase):
    def setUp(self):
        self.redis = redis.Redis(host='localhost', port=7575, db=0)
        self.redis.flushall()
