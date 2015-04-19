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

import time

import venture.ripl.utils as u

def __venture_start__(ripl):
    ripl.bind_callback("hmm_start_timer", hmm_start_timer)
    ripl.bind_callback("hmm_map", hmm_map)
    ripl.bind_callback("hmm_smoothed", hmm_smoothed)
    ripl.bind_callback("hmm_smoothed_nw", hmm_smoothed_nw)
    ripl.bind_callback("hmm_begin", hmm_begin)
    ripl.bind_callback("hmm_state", hmm_state)
    ripl.bind_callback("hmm_end", hmm_end)

hmm_start_time = None
hmm_downtime = None
def hmm_start_timer(inferrer):
    global hmm_start_time
    global hmm_downtime
    hmm_start_time = time.time()
    hmm_downtime = 0
def hmm_time():
    assert hmm_start_time is not None
    assert hmm_downtime is not None
    return time.time() - hmm_start_time - hmm_downtime

hmm_downtime_start = None
def hmm_pause():
    global hmm_downtime_start
    assert hmm_downtime_start is None
    hmm_downtime_start = time.time()
def hmm_resume():
    global hmm_downtime_start
    global hmm_downtime
    assert hmm_downtime_start is not None
    hmm_downtime += time.time() - hmm_downtime_start
    hmm_downtime_start = None

def hmm_map(inferrer, states):
    sequence = map(int, u.strip_types(states[0]))
    time = hmm_time()
    hmm_pause()
    import sys
    print >>sys.stderr, 'MAP sequence: %s' % (sequence,)
    print >>sys.stderr, 'Score: %s' % inferrer.engine.logscore()
    print '%s,%s' % (time, metric1(sequence))
    hmm_resume()

def hmm_smoothed(inferrer, states, likelihood_weight = True):
    states = u.strip_types(states)
    n = len(states[0])
    marginals = [marginalize(inferrer, [s[i] for s in states], likelihood_weight)
        for i in range(n)]
    time = hmm_time()
    hmm_pause()
    for i in range(n):
        import sys
        tvd = total_variation_distance(marginals[i], smoothed_marginals[i])
        print >>sys.stderr, ('Smoothed marginals at %2d (tvd %s): %s' %
            (i, tvd, marginals[i]))
    m, v = metric2(marginals)
    print '%s,%s,%s' % (time, m, v)
    hmm_resume()

def hmm_smoothed_nw(inferrer, states):
    hmm_smoothed(inferrer, states, False)

hmm_marginals = None
def hmm_begin(inferrer):
    global hmm_marginals
    assert hmm_marginals is None
    hmm_marginals = []
def hmm_state(inferrer, states):
    global hmm_marginals
    assert hmm_marginals is not None
    import sys
    marginals = marginalize(inferrer, u.strip_types(states))
    tvd = total_variation_distance(marginals, filtered_marginals[len(hmm_marginals)])
    print >>sys.stderr, ('Filtered marginals at %2d (tvd %s): %s' %
        (len(hmm_marginals), tvd, marginals,))
    hmm_marginals.append(marginals)
def hmm_end(inferrer):
    global hmm_marginals
    assert hmm_marginals is not None
    time = hmm_time()
    hmm_pause()
    m, v = metric3(hmm_marginals)
    print '%s,%s,%s' % (time, m, v)
    hmm_marginals = None
    hmm_resume()

def marginalize(inferrer, states, likelihood_weight = True):
    if likelihood_weight:
        weights = inferrer.particle_normalized_probs()
        total = sum(weights)
    else:
        weights = [1 for _ in states]
        total = len(states)
    histogram = [0 for _ in range(5)]
    #print "st/wt", zip(states, weights)
    for (state, w) in zip(states, weights):
        histogram[int(state)-1] += w
    return [h / float(total) for h in histogram]

def metric1(states):
    return minimum(lambda map: hamming_distance(states, map), maps)

def metric2(marginals):
    return mvtvd(marginals, smoothed_marginals)

def metric3(marginals):
    return mvtvd(marginals, filtered_marginals)

maps = [
    [1, 2, 3, 5, 5, 1, 2, 2, 2, 4, 4, 1, 2, 2, 2, 4, 1, 3, 5, 1],
    [1, 2, 3, 5, 5, 1, 2, 2, 2, 4, 4, 1, 2, 2, 3, 4, 1, 3, 5, 1],
    [1, 2, 3, 5, 5, 1, 2, 2, 2, 4, 4, 1, 2, 2, 4, 4, 1, 3, 5, 1],
    [1, 2, 3, 5, 5, 1, 2, 2, 2, 4, 4, 1, 2, 2, 2, 2, 2, 3, 5, 1],
    [1, 2, 3, 5, 5, 1, 2, 2, 2, 4, 4, 1, 2, 2, 3, 5, 2, 3, 5, 1],
    [1, 2, 3, 5, 5, 1, 2, 2, 2, 4, 4, 1, 2, 2, 4, 5, 2, 3, 5, 1],
    [1, 2, 3, 5, 5, 1, 2, 2, 2, 4, 4, 1, 2, 2, 4, 1, 2, 3, 5, 1],
    [1, 2, 3, 5, 5, 1, 2, 2, 2, 4, 4, 1, 2, 4, 1, 1, 2, 3, 5, 1],
    [1, 2, 3, 5, 5, 1, 2, 2, 2, 4, 4, 1, 2, 4, 1, 2, 2, 3, 5, 1],
    [1, 2, 3, 5, 5, 1, 3, 5, 2, 4, 4, 1, 2, 2, 2, 4, 1, 3, 5, 1],
    [1, 2, 3, 5, 5, 1, 3, 5, 2, 4, 4, 1, 2, 2, 3, 4, 1, 3, 5, 1],
    [1, 2, 3, 5, 5, 1, 3, 5, 2, 4, 4, 1, 2, 2, 4, 4, 1, 3, 5, 1],
    [1, 2, 3, 5, 5, 1, 3, 5, 2, 4, 4, 1, 2, 2, 2, 2, 2, 3, 5, 1],
    [1, 2, 3, 5, 5, 1, 3, 5, 2, 4, 4, 1, 2, 2, 3, 5, 2, 3, 5, 1],
    [1, 2, 3, 5, 5, 1, 3, 5, 2, 4, 4, 1, 2, 2, 4, 5, 2, 3, 5, 1],
    [1, 2, 3, 5, 5, 1, 3, 5, 2, 4, 4, 1, 2, 2, 4, 1, 2, 3, 5, 1],
    [1, 2, 3, 5, 5, 1, 3, 5, 2, 4, 4, 1, 2, 4, 1, 1, 2, 3, 5, 1],
    [1, 2, 3, 5, 5, 1, 3, 5, 2, 4, 4, 1, 2, 4, 1, 2, 2, 3, 5, 1],
]

smoothed_marginals = [
    # From Galois's solution.
    [1, 0, 0, 0, 0],
    [0.112809148, 0.752717036, 0.134473816, 0, 0],
    [0.00317542, 0.034865037, 0.837224069, 0.110733778, 0.014001696],
    [0.004693437, 0.004584395, 0.1200948, 0.144261127, 0.726366241],
    [0.119500534, 0.041244252, 0.008241435, 0.035750153, 0.795263626],
    [0.684607699, 0.151517642, 0.033403961, 0.018330183, 0.112140515],
    [0.109597964, 0.480893286, 0.280132093, 0.064420886, 0.06495577],
    [0.065186797, 0.401069226, 0.110539353, 0.06486809, 0.358336534],
    [0.028664143, 0.699619091, 0.109896758, 0.13474607, 0.027073938],
    [0.010294305, 0.102091819, 0.11002734, 0.761263645, 0.01632289],
    [0.106671515, 0.006779434, 0.009033973, 0.751579763, 0.125935315],
    [0.787750458, 0.033343101, 0.007848604, 0.041442547, 0.12961529],
    [0.13124567, 0.744065332, 0.070170825, 0.016864823, 0.037653351],
    [0.046347729, 0.567514651, 0.111527671, 0.232243809, 0.042366141],
    [0.225255836, 0.181743541, 0.203408654, 0.307877447, 0.081714522],
    [0.239364938, 0.202351937, 0.057624408, 0.297890753, 0.202767964],
    [0.239579829, 0.515082411, 0.102402753, 0.08725375, 0.055681256],
    [0.026657056, 0.0344331, 0.720097436, 0.130808954, 0.088003453],
    [0.043516394, 0.0175655, 0.049705872, 0.133667507, 0.755544727],
    [0.699546471, 0.105737807, 0.02786334, 0.039132229, 0.127720153],
]

filtered_marginals = [
    # Generated by HMM.hs.
    [1.00000000,0.00000000,0.00000000,0.00000000,0.00000000],
    [0.12500000,0.75000000,0.12500000,0.00000000,0.00000000],
    [0.01562500,0.10937500,0.75000000,0.10937500,0.01562500],
    [0.01906780,0.01906780,0.11864407,0.13135593,0.71186441],
    [0.11041780,0.09603907,0.02007596,0.03445469,0.73901248],
    [0.71478719,0.12743162,0.03053240,0.02029399,0.10695480],
    [0.10870776,0.73523608,0.11267313,0.02301330,0.02036972],
    [0.04023267,0.22863740,0.25305448,0.23038567,0.24768979],
    [0.09284019,0.55516220,0.09348797,0.12754848,0.13096117],
    [0.05106092,0.11320510,0.10775920,0.67681971,0.05115506],
    [0.10402510,0.02876531,0.03632369,0.71928984,0.11159606],
    [0.73091743,0.03184373,0.02203569,0.10220512,0.11299803],
    [0.12822154,0.71211552,0.10635839,0.02115312,0.03215143],
    [0.02465569,0.71103183,0.12858443,0.11404191,0.02168614],
    [0.25310968,0.19920827,0.22732521,0.25083603,0.06952081],
    [0.08978867,0.08170522,0.10641293,0.63634164,0.08575155],
    [0.18941643,0.36010051,0.06483716,0.19235093,0.19329496],
    [0.09471081,0.12233860,0.60709222,0.10166534,0.07419303],
    [0.03912926,0.04211899,0.11918598,0.12019174,0.67937402],
    [0.69954647,0.10573781,0.02786334,0.03913223,0.12772015],
]

def hamming_distance(a, b):
    h = 0
    for x, y in zip(a, b):
        h += bitcount(x ^ y)
    return h

def bitcount(n):
    if n < 0:                     # paranoia
        n = ~n
    c = 0
    while n != 0:
        c += n & 1
        n >>= 1
    return c

def minimum(f, i):
    i = iter(i)
    x0 = i.next()
    y0 = f(x0)
    for x in i:
        y = f(x)
        if y < y0:
            y0 = y
    return y0

# Mean and Variance of Total Variation Distances
def mvtvd(actual, expected):
    tvds = [total_variation_distance(a, e) for a, e in zip(actual, expected)]
    mean = sum(tvds) / len(tvds)
    variance = sum((t - mean)**2 for t in tvds)
    return (mean, variance)

def total_variation_distance(p, q):
    return sum(abs(x - y) for x, y in zip(p, q)) / 2
