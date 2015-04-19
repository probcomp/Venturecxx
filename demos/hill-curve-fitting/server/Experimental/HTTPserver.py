# Copyright (c) 2015 MIT Probabilistic Computing Project.
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
# You should have received a copy of the GNU General Public License
# along with Venture.  If not, see <http://www.gnu.org/licenses/>.

from flask import Flask, json, request, make_response, current_app
from venture.shortcuts import *
from venture.exception import VentureException
from datetime import timedelta
from functools import update_wrapper

class VentureServer(Flask):
	def __init__(self, name):
		super(VentureServer, self).__init__(name)
		self.ripl = make_church_prime_ripl()

#from http://flask.pocoo.org/snippets/56/
def crossdomain(origin=None, methods=None, headers=None,
				max_age=21600, attach_to_all=True,
				automatic_options=True):
	if methods is not None:
		methods = ', '.join(sorted(x.upper() for x in methods))
	if headers is not None and not isinstance(headers, basestring):
		headers = ', '.join(x.upper() for x in headers)
	if not isinstance(origin, basestring):
		origin = ', '.join(origin)
	if isinstance(max_age, timedelta):
		max_age = max_age.total_seconds()

	def get_methods():
		if methods is not None:
			return methods

		options_resp = current_app.make_default_options_response()
		return options_resp.headers['allow']

	def decorator(f):
		def wrapped_function(*args, **kwargs):
			if automatic_options and request.method == 'OPTIONS':
				resp = current_app.make_default_options_response()
			else:
				resp = make_response(f(*args, **kwargs))
			if not attach_to_all and request.method != 'OPTIONS':
				return resp

			h = resp.headers

			h['Access-Control-Allow-Origin'] = origin
			h['Access-Control-Allow-Methods'] = get_methods()
			h['Access-Control-Max-Age'] = str(max_age)
			if headers is not None:
				h['Access-Control-Allow-Headers'] = headers
			return resp

		f.provide_automatic_options = False
		return update_wrapper(wrapped_function, f)
	return decorator

app = VentureServer(__name__)

ripl_methods = ['assume', 'observe', 'infer', 'sample', 'forget', 'start_continuous_inference', 'stop_continuous_inference', 'clear']

def makeCall(call):
	try:
		method = call['method']
		args = call['args']
		if method in ripl_methods:
			return {'result': getattr(app.ripl, method)(*args)}
		return {'error': "Bad method"}
	except VentureException as e:
		return {'error': "VentureException: " + str(e)}
	except Exception as e:
		return {'error': "Exception: " + str(e)}

@app.route('/venture', methods=['POST', 'OPTIONS'])
@crossdomain(origin='*', headers=['Content-Type'])
def ventureCall():
	try:
		j = request.get_json()
		calls = j['calls']
		results = map(makeCall, calls)
		return json.dumps({'results': results})
	except Exception:
		return json.dumps({'error': "Bad JSON"})

if __name__ == '__main__':
	app.debug = True
	app.run()