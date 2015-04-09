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

from flask import Flask, session
from flask.ext.socketio import SocketIO, emit, join_room, close_room
from venture.shortcuts import *
import os, time, threading

app = Flask(__name__)
# A secret key is required for sessions to work
# For testing it's fine to just inline it here, but ideally it should be loaded from a configuration file
# Generated with os.urandom
app.config['SECRET_KEY'] = '9b4847b67ea066e14bd0c2e6ff098b4925a02873bc8fb604'
socketio = SocketIO(app)

@socketio.on('initialize', namespace='/venture')
def initialize():
	"""Initialize the generative model"""
	ripl = session['ripl']
	ripl.clear()

	# The function parameters are estimated with the help of the user-defined graph parameters
	# This gives an estimate of where the data should fall, as presumably the user wants all points to be visible on the graph
	ripl.assume('gminx', '(normal -3 0.1)')
	ripl.assume('gmaxx', '(normal 3 0.1)')
	ripl.assume('gminy', '(normal 0 0.1)')
	ripl.assume('gmaxy', '(normal 1 0.1)')
	ripl.observe('gminx', '-3', 'observe_gminx')
	ripl.observe('gmaxx', '3', 'observe_gmaxx')
	ripl.observe('gminy', '0', 'observe_gminy')
	ripl.observe('gmaxy', '1', 'observe_gmaxy')

	ripl.assume('abs', '(lambda (x) (if (gt x 0) x (- 0 x)))')

	# Estimate the prior for the parameters
	ripl.assume('log_ic50', '(normal (/ (+ gmaxx gminx) 2) (/ (- gmaxx gminx) 4))')
	ripl.assume('ic50', '(pow 10 log_ic50)')
	ripl.assume('mid', '(normal (/ (+ gmaxy gminy) 2) (/ (- gmaxy gminy) 4))')
	ripl.assume('diff', '(abs (normal (/ (- gmaxy gminy) 4) (/ (- gmaxy gminy) 8)))')
	ripl.assume('max', '(+ mid diff)')
	ripl.assume('min', '(- mid diff)')
	ripl.assume('slope', '(normal 0 2)')
	ripl.assume('noise', '(normal 0 (/ (- gmaxy gminy) 16))')

	# Each point has some probability of being an outlier
	ripl.assume('p_outlier', '(beta 1 20)')
	ripl.assume('is_outlier', '(mem (lambda (x) (flip p_outlier)))')

	# Finally, assemble the function
	# u is just a helper function since it's used twice
	# f is the function we care about
	# y is the noisy function, which also accounts for outliers
	ripl.assume('u', '(lambda (x) (pow (/ x ic50) slope))')
	ripl.assume('f', '(lambda (x) (+ (/ (* (- max min) (u x)) (+ (u x) 1)) min))')
	ripl.assume('y', '(lambda (x) (if (is_outlier x) (normal mid (/ diff 2)) (normal (f x) noise)))')

@socketio.on('addPoint', namespace='/venture')
def addPoint(data):
	"""Observe a point on the graph"""
	ripl = session['ripl']
	x = data['x']
	y = data['y']
	# Give the observation a label so it can be forgotten by the RIPL
	ripl.label += 1
	point_label = 'point_' + str(ripl.label)
	ripl.point_labels[(x, y)] = point_label
	ripl.observe('(y ' + str(x) + ')', str(y), point_label)

@socketio.on('removePoint', namespace='/venture')
def removePoint(data):
	"""Unobserve a point on the graph"""
	ripl = session['ripl']
	ripl.forget(ripl.point_labels[(data['x'], data['y'])])

@socketio.on('observeGrid', namespace='/venture')
def observeGrid(data):
	"""Observe the graph parameters"""
	ripl = session['ripl']
	ripl.forget('observe_gminx')
	ripl.forget('observe_gmaxx')
	ripl.forget('observe_gminy')
	ripl.forget('observe_gmaxy')
	ripl.observe('gminx', str(data['gminx']), 'observe_gminx')
	ripl.observe('gmaxx', str(data['gmaxx']), 'observe_gmaxx')
	ripl.observe('gminy', str(data['gminy']), 'observe_gminy')
	ripl.observe('gmaxy', str(data['gmaxy']), 'observe_gmaxy')

class Sampler(threading.Thread):
	"""Class handling automatic sampling of variables"""
	def __init__(self, ripl, room, params, stop_event):
		self.ripl = ripl
		self.room = room
		self.params = params
		self.stop_event = stop_event
		super(Sampler, self).__init__()

	def run(self):
		while not self.stop_event.isSet():
			# It would be nice to have a better way to integrate continuous sampling and continuous inference, but this works for now
			self.ripl.infer(self.params)
			ic50 = self.ripl.sample('ic50')
			min_ = self.ripl.sample('min')
			max_ = self.ripl.sample('max')
			slope = self.ripl.sample('slope')
			noise = self.ripl.sample('noise')
			outliers = filter(lambda point: self.ripl.sample('(is_outlier ' + str(point[0]) + ')'), self.ripl.point_labels.keys())
			time.sleep(0.1) # Without this, the server cannot receive messages, and instead spends all its time in this loop. Probably evidence that something is wrong here...
			socketio.emit('sample', {'ic50': ic50, 'min': min_, 'max': max_, 'slope': slope, 'noise': noise, 'outliers': outliers}, namespace='/venture', room=self.room)
			# TODO: consider only returning results that have changed since the last iteration

@socketio.on('startSample', namespace='/venture')
def startSample(data):
	"""Start continuous sampling"""
	ripl = session['ripl']
	# When the sampler starts running in its own thread, the request context for the client is no longer available
	# Translation: the standard 'emit' function won't work
	# We get around this by adding the client to a randomly named room, then broadcasting to the entire room
	# Since there is one client per room, this accomplishes the desired effect
	sample_room = os.urandom(10).encode('hex')
	join_room(sample_room)
	sampler = Sampler(ripl, sample_room, data['params'], threading.Event())
	session['sampler'] = sampler
	sampler.start()

@socketio.on('stopSample', namespace='/venture')
def stopSample():
	"""Stop continuous sampling"""
	sampler = session['sampler']
	sampler.stop_event.set()
	close_room(sampler.room)

@socketio.on('startInference', namespace='/venture')
def startInference(data):
	"""Start continuous inference. Intended for use with the sample method below."""
	ripl = session['ripl']
	ripl.start_continuous_inference(data['params'])

@socketio.on('stopInference', namespace='/venture')
def stopInference():
	"""Stop continuous inference"""
	ripl = session['ripl']
	ripl.stop_continuous_inference()

@socketio.on('sample', namespace='/venture')
def sample():
	"""Returns a single sample to the client"""
	ripl = session['ripl']
	status = ripl.continuous_inference_status()
	if status['running']:
		ripl.stop_continuous_inference()
	# If we don't stop inference, sampling can be particularly slow because it tries to run an iteration of inference between every sample
	# This is very pronounced when we have lots of points to sample for outliers
	ic50 = ripl.sample('ic50')
	min_ = ripl.sample('min')
	max_ = ripl.sample('max')
	slope = ripl.sample('slope')
	noise = ripl.sample('noise')
	outliers = filter(lambda point: ripl.sample('(is_outlier ' + str(point[0]) + ')'), ripl.point_labels.keys())
	if status['running']:
		params = '(' + ' '.join(map(lambda exp: str(exp['value']), status['expression'])) + ')'
		ripl.start_continuous_inference(params)
	emit('sample', {'ic50': ic50, 'min': min_, 'max': max_, 'slope': slope, 'noise': noise, 'outliers': outliers})

@socketio.on('connect', namespace='/venture')
def connect():
	"""Perform initialization when a client connects"""
	ripl = make_church_prime_ripl()
	ripl.label = 0
	ripl.point_labels = {}
	session['ripl'] = ripl

@socketio.on('disconnect', namespace='/venture')
def disconnect():
	"""Perform cleanup when a client disconnects"""
	ripl = session['ripl']
	ripl.stop_continuous_inference()
	ripl.clear()
	# TODO: Ensure that the RIPL and all other session data gets garbage collected to prevent memory leaks

if __name__ == '__main__':
	#app.debug = True
	socketio.run(app)