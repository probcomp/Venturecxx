from flask import Flask, json, request, make_response, current_app
from venture.shortcuts import *
from venture.exception import VentureException
from datetime import timedelta
from functools import update_wrapper

class VentureServer(Flask):
	def __init__(self, name):
		super(VentureServer, self).__init__(name)
		self.the_ripl = make_church_prime_ripl()
		self.the_ripl.label = 0
		self.the_ripl.point_labels = {}

	def initialize(self):
		ripl = self.the_ripl
		ripl.clear()
		ripl.assume('gminx', '(normal -3 0.1)')
		ripl.assume('gmaxx', '(normal 3 0.1)')
		ripl.assume('gminy', '(normal 0 0.1)')
		ripl.assume('gmaxy', '(normal 1 0.1)')
		ripl.observe('gminx', '-3', 'observe_gminx')
		ripl.observe('gmaxx', '3', 'observe_gmaxx')
		ripl.observe('gminy', '0', 'observe_gminy')
		ripl.observe('gmaxy', '1', 'observe_gmaxy')

		ripl.assume('abs', '(lambda (x) (if (gt x 0) x (- 0 x)))')

		ripl.assume('log_ic50', '(normal (/ (+ gmaxx gminx) 2) (/ (- gmaxx gminx) 4))')
		ripl.assume('ic50', '(pow 10 log_ic50)')
		ripl.assume('mid', '(normal (/ (+ gmaxy gminy) 2) (/ (- gmaxy gminy) 4))')
		ripl.assume('diff', '(abs (normal (/ (- gmaxy gminy) 4) (/ (- gmaxy gminy) 8)))')
		ripl.assume('max', '(+ mid diff)')
		ripl.assume('min', '(- mid diff)')
		ripl.assume('slope', '(normal 0 1)')
		ripl.assume('noise', '(normal 0 (/ (- gmaxy gminy) 8))')

		ripl.assume('u', '(lambda (x) (pow (/ x ic50) slope))')
		ripl.assume('f', '(lambda (x) (+ (/ (* (- max min) (u x)) (+ (u x) 1)) min))')
		ripl.assume('y', '(lambda (x) (normal (f x) noise))')

	def startInference(self, params):
		ripl = self.the_ripl
		ripl.start_continuous_inference(params)

	def stopInference(self):
		ripl = self.the_ripl
		ripl.stop_continuous_inference()

	def addPoint(self, x, y):
		ripl = self.the_ripl
		ripl.label += 1
		point_label = 'point_' + str(ripl.label)
		ripl.point_labels[(x, y)] = point_label
		ripl.observe('(y ' + str(x) + ')', str(y), point_label)

	def removePoint(self, x, y):
		ripl = self.the_ripl
		ripl.forget(ripl.point_labels[(x, y)])

	def observeGrid(self, gminx, gmaxx, gminy, gmaxy):
		ripl = self.the_ripl
		ripl.forget('observe_gminx')
		ripl.forget('observe_gmaxx')
		ripl.forget('observe_gminy')
		ripl.forget('observe_gmaxy')
		ripl.observe('gminx', str(gminx), 'observe_gminx')
		ripl.observe('gmaxx', str(gmaxx), 'observe_gmaxx')
		ripl.observe('gminy', str(gminy), 'observe_gminy')
		ripl.observe('gmaxy', str(gmaxy), 'observe_gmaxy')

	def sample(self):
		ripl = self.the_ripl
		ic50 = ripl.sample('ic50')
		min_ = ripl.sample('min')
		max_ = ripl.sample('max')
		slope = ripl.sample('slope')
		noise = ripl.sample('noise')
		return {'ic50': ic50, 'min': min_, 'max': max_, 'slope': slope, 'noise': noise}

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

methods = ['initialize', 'startInference', 'stopInference', 'addPoint', 'removePoint', 'observeGrid', 'sample']

def makeCall(call):
	try:
		method = call['method']
		args = call['args']
		if method in methods:
			result = getattr(app, method)(*args)
			if result == None:
				return {}
			return result
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