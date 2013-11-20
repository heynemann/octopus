#!/usr/bin/env python
# -*- coding: utf-8 -*-

from preggy import expect

from octopus.model import Response
from tests import TestCase


class TestResponseModel(TestCase):
    def test_can_create_response(self):
        response = Response(
            url="http://www.google.com",
            status_code=200,
            headers={
                'Accept': 'image/webp; */*'
            },
            cookies={
                'whatever': 'some-value'
            },
            text='some request body',
            effective_url='http://www.google.com/',
            error="some error message",
            request_time=10.24
        )

        expect(response.url).to_equal('http://www.google.com')
        expect(response.status_code).to_equal(200)
        expect(response.headers).to_be_like({
            'Accept': 'image/webp; */*'
        })
        expect(response.cookies).to_be_like({
            'whatever': 'some-value'
        })
        expect(response.text).to_equal('some request body')
        expect(response.effective_url).to_equal('http://www.google.com/')
        expect(response.error).to_equal('some error message')
        expect(response.request_time).to_equal(10.24)
