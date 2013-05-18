#!/usr/bin/env python
# -*- coding: utf-8 -*-

from venture.exception import VentureException


def substitute_params(s, params, parser):
    out = []
    if isinstance(params, (tuple, list)):
        i = 0
        j = 0
        while i < len(s):
            if s[i] == "%":
                if i + 1 >= len(s) or s[i+1] not in ['%','s','v']:
                    raise VentureException('fatal', 'Param substitution failure. '
                        'Dangling "%" at index ' + str(i))
                i += 1
                if s[i] == '%':
                    out.append('%')
                if s[i] in ['s','v']:
                    if j >= len(params):
                        raise VentureException('fatal', 'Param substitution failure. '
                                'Not enough params provided')
                    if s[i] == 's':
                        out.append(str(params[j]))
                    if s[i] == 'v':
                        out.append(parser.value_to_string(params[j]))
                    j += 1
            else:
                out.append(s[i])
            i += 1
        if j < len(params):
            raise VentureException('fatal', 'Param substitution failure. '
                    'Too many params provided')
    elif isinstance(params, dict):
        i = 0
        while i<len(s):
            if s[i] == "%":
                if i + 1 >= len(s) or s[i+1] not in ['%','(']:
                    raise VentureException('fatal', 'Param substitution failure. '
                        'Dangling "%" at index ' + str(i))
                i += 1
                if s[i] == '%':
                    out.append('%')
                if s[i] == '(':
                    j = i
                    p = 1
                    while p > 0:
                        j += 1
                        if j >= len(s):
                            raise VentureException('fatal', 'Param substitution failure. '
                                'Incomplete "%" expression starting at index ' + str(i-1))
                        if s[j] == ')':
                            p -= 1
                    if j+1 >= len(s) or s[j+1] not in ['s','v']:
                        raise VentureException('fatal', 'Param substitution failure. '
                            'Expected "s" or "v" after index ' + str(j))
                    key = s[i+1:j]
                    if not key in params:
                        raise VentureException('fatal', 'Param substitution failure. '
                                'Key not present in params dict: ' + key)
                    c = s[j+1]
                    if c == 's':
                        out.append(str(params[key]))
                    if c == 'v':
                        out.append(parser.value_to_string(params[key]))
                    i = j+1
            else:
                out.append(s[i])
            i += 1
    return ''.join(out)