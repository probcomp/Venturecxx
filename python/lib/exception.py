# Copyright (c) 2013, MIT Probabilistic Computing Project.
#
# This file is part of Venture.
#
# Venture is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Venture is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with Venture.  If not, see <http://www.gnu.org/licenses/>.
#!/usr/bin/env python
# -*- coding: utf-8 -*-


class VentureException(Exception):
    def __init__(self, exception, message=None, **kwargs):
        if message is None: # Only one argument version
            message = exception
            exception = ""
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
        s = "*** " + self.exception + ": " + self.message
        # TODO exceptions need to be annotated to get an 'instruction_string'
        # perhaps this should not be done in the ripl but in the parser itself?
        if self.exception in ['parse', 'text_parse', 'invalid_argument'] and 'instruction_string' in self.data:
          s += '\n' + self.data['instruction_string']
          offset = self.data['text_index'][0]
          length = self.data['text_index'][1] - offset + 1
          s += '\n' + ''.join([' '] * offset + ['^'] * length)
        else:
          s += '\n' + str(self.data)
        return s

    __unicode__ = __str__
    __repr__ = __str__

def exception_eq(ex1, ex2):
    '''Returns True if two exceptions are of same type and have same message'''
    return (type(ex1) == type(ex2)) and (ex1.args == ex2.args)

def exception_all_eq(ex_list):
    '''Returns True if all exceptions in a list are equal'''
    same = [exception_eq(ex_list[0], ex) for ex in ex_list[1:]]
    return all(same)

def exception_type_eq(ex_list):
    '''Returns True if all exceptions in list are of same type, else False'''
    same = [type(ex_list[0]) is type(ex) for ex in ex_list[1:]]
    return all(same)
