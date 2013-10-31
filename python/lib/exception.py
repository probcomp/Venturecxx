#!/usr/bin/env python
# -*- coding: utf-8 -*-


class VentureException(Exception):
    def __init__(self, exception, message, **kwargs):
        self.exception = exception
        self.message = message
        self.data = kwargs

    def to_json_object(self):
        d = {
                "exception" : self.exception,
                "message" : self.message,
                }
        d.update(self.data)
        return d

    @classmethod
    def from_json_object(cls, json_object):
        data = json_object.copy()
        exception = data.pop('exception')
        message = data.pop('message')
        return cls(exception,message,**data)

    def __str__(self):
        return self.exception + " -- " + self.message + " " + str(self.data)
    __unicode__ = __str__
    __repr__ = __str__