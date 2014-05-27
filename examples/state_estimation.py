import matplotlib
matplotlib.use("Agg")

import time
import math
import numpy as np
import numpy.random as npr
import venture.test.randomized
import venture.venturemagics.ip_parallel
from venture.shortcuts import *
from venture.lite.trace import *
from venture.lite.sp import *
from venture.lite.regen import *
from venture.lite.psp import *
from venture.lite.builtin import *
from venture.lite import value

#
# FIXME: dummy simplest thing running
# FIXME: add stubs for python sps
# FIXME: make nontrivial python sps
# FIXME: 


def init(ripl):
    """
    Initialize a ripl with the Venture program for state estimation.
    """

    program = """

    [ASSUME map (lambda (proc lst) (if (eq lst nil) nil (pair (proc (first lst)) (map proc (rest lst))) ))]
    [ASSUME range (lambda (min max) (if (eq min max) nil (pair min (range (+ min 1) max))))]

    [ASSUME num_landmarks 3]
    [ASSUME gen_landmark (lambda (id) (list (uniform_continuous 0 1) (uniform_continuous 0 1)))]
    map: [ASSUME slam_map (map gen_landmark (range 0 num_landmarks))]

    [ASSUME get_control (mem (lambda (t coord) (normal 0 1)))]
    [ASSUME gen_pose (lambda () (list (uniform_continuous 0 1) (uniform_continuous 0 1) (normal 0 1)))]
    [ASSUME simulate_motion (lambda (pose control) (gen_pose))]

    [ASSUME dist (lambda (landmark pose) (gamma 1 1))]
    [ASSUME obs_sigma (gamma 1 1)]

    [ASSUME get_pose (mem (lambda (i) (if (= i 0)
            (list (uniform_continuous 0 1) (uniform_continuous 0 1) (uniform_continuous 0 1))
            (simulate_motion (get_pose (- i 1)) (list (get_control i 0) (get_control i 1)))
            )))]

    [ASSUME get_gps (mem (lambda (i) (normal 0 1)))]
    [ASSUME range_noise (gamma 1 1)]
    [ASSUME intensity_noise (gamma 1 1)]
    [ASSUME get_laser (mem (lambda (i) (simulate_laser (get_pose i) slam_map range_noise intensity_noise)))]
"""
    prog_split = program.split('\n')
    for i in range(len(prog_split)):
        line = prog_split[i]
        if len(line) > 0:
            ripl.execute_program(line)

    print "INITIAL MAP: " + str(ripl.report("map"))

def gen_laser(raw):
    observations = [{'type': 'list', 'value': [number(l[0]), number(l[1])]} for l in raw]
    laser_val = {'type': 'list', 'value': observations}
    return laser_val

def observe(ripl, t, control, gps, laser):
    """
    Add the given gps and laser observations to the ripl at time t.
    """

    ripl.observe("(get_control %i 0)" % t, control[0])
    ripl.observe("(get_control %i 1)" % t, control[1])

    if gps is not None:
        ripl.observe("(get_gps %i %s)" % (t, control_str), gps)
    if laser is not None:
        ripl.observe("(get_laser %i)" % t, gen_laser(laser))


def read_scene(ripl, t=0):
    """
    Extract belief state from ripl, compatible with mripl (or with a weighted particle reporting option)
    """
    #print "RIPL contents: \n"
    #import pprint
    #pprint.pprint(ripl.list_directives())

    out = {}
    out["map"] = ripl.sample("slam_map")
    out["pose"] = ripl.sample("(get_pose %i)" % t)

    # FIXME: reinstate: if we are not an mripl, wrap in a list so we can reuse plotting
    #    if not isinstance(ripl, venture.venturemagics.ip_parallel.MRipl):
    out["map"] = [out["map"]]
    out["pose"] = [out["pose"]]

    return out

def merge_scene(a, b):
    out = {}
    import pprint
    #print "merging:"
    #pprint.pprint(a["map"])
    #pprint.pprint(b["map"])
    out["map"] = a["map"] + b["map"]
    out["pose"] = a["pose"] + b["pose"]
    return out
    
def gen_map(num_landmarks=3):
    return [(npr.random(), npr.random()) for i in range(num_landmarks)]

def gen_pose():
    return (npr.random(), npr.random(), npr.random() * 2 * math.pi)

def gen_control():
    return ((npr.random() - 0.5) * math.pi, npr.random() / 20.0)

def simulate_motion(pose, dtheta, r):
    """
    Real motion model: a jittered control
    """
    dtheta += (npr.random() - 0.5) * math.pi / 5.0
    r *= npr.random() + 0.5

    return (pose[0] + (r * math.cos(dtheta)), pose[1] + (r * math.sin(dtheta)), pose[2] + dtheta)

def simulate_laser(pose, slam_map, range_noise, intensity_noise):
    """
    Real sensor error model: noise on the true distances
    """
    args = venture.test.randomized.BogusArgs([pose, slam_map, range_noise, intensity_noise], None)
    laser = SimulateLaserPSP()
    return laser.simulate(args)

# FIXME add gps sim

def display(t, prefix="scene_", scene=None, true_map=None, true_pose=None, verbose=True):
    """
    Render a scene
    """
    filename = prefix + "%05i" % t + ".png"
    if verbose:
        print "--- saving frame %05i to filename %s" % (t, filename)
    
    from PIL import Image, ImageDraw
    D = 500
    im = Image.new('RGB', (D, D))
    draw = ImageDraw.Draw(im)
    
    grey  = (128, 128, 128)
    blue  = (100, 100, 200)
    red   = (200, 100, 100)
    green = (100, 200, 100)
    
    def scale(x):
        return x * D

    def draw_map(map, draw, color, offset=0):
        for landmark in map:
            #print "landmark: " + str(landmark)
            x = scale(landmark[0])
            y = scale(landmark[1])
            draw.ellipse([(x - offset, y - offset), (x + offset, y + offset)], fill=color)

    def draw_pose(pose, draw, color, offset=0):
        x = scale(pose[0])
        y = scale(pose[1])
        theta = pose[2]
        draw.ellipse([(x - offset, y - offset), (x + offset, y + offset)], fill=color)
        draw.line([(x, y), (x + float(3 * offset) * math.cos(theta), y + float(3 * offset) * math.sin(theta))], fill=color)

    if scene is not None:
        if "map" in scene:
            [draw_map(m, draw, grey, offset=1) for m in scene["map"]]
        if "pose" in scene:
            [draw_pose(p, draw, blue, offset=1) for p in scene["pose"]]

    if verbose:
        import pprint
        print "--- scene:"
        pprint.pprint(scene)

        pprint.pprint("--- truth:")
        pprint.pprint(true_map)
        pprint.pprint(true_pose)

    draw_map(true_map, draw, red, offset=2)
    draw_pose(true_pose, draw, green, offset=2)

    im.save(open(filename, 'w'))
    return im

def run_test(num_steps=1, ripl=None, num_infers=10):

    scene = None

    if ripl is not None:
        init(ripl)

    #synth_ripl = make_lite_church_prime_ripl()
    #init(synth_ripl)
    #
    #true_map = synth_ripl.sample('slam_map')
    #true_pose = synth_ripl.sample('(get_pose 0)')

    count = 0

    logscores = []
    scenes = []

    true_map = [[npr.random(), npr.random()] for i in range(3)]
    true_pose = [npr.random() for i in range(3)]
    laser = simulate_laser(true_pose, true_map, 0.1, 0.1)

    for i in range(num_steps):
        (dtheta, r) = gen_control()

        true_pose = simulate_motion(true_pose, dtheta, r)
        laser     = simulate_laser(true_pose, true_map, 0.1, 0.1)
        # FIXME: num_landmarks (and map generation above); range and intensity noise parameters here and above

        if ripl is not None:
            observe(ripl, i, (dtheta, r), None, laser)

            tmp = {"map": [], "pose": []}

            for j in range(num_infers):
                new_scores, intermediate_scenes = infer(ripl, i, 1)
                scene = intermediate_scenes[-1]

                logscores = logscores + new_scores
                scenes = scenes + intermediate_scenes

    print "LOGSCORES: "
    import pprint
    pprint.pprint(logscores)

    #import seaborn as sns
    #import matplotlib.pyplot as plt
    #sns.set(palette="Set2")
    #sns.tsplot(logscores)
    #plt.savefig("logscores.png")
    
def test_simple():
    # 
    true_pose = [0.25, 0.5, 0.0]
    true_map  = [[0.75, 0.5]]
    laser = simulate_laser(true_pose, true_map, 0.05, 0.05)

    num_ripls = 100
    print "******** creating ripls"

    print "Remote: " + str(num_ripls) + " ripls"
    mripl = venture.venturemagics.ip_parallel.MRipl(num_ripls, backend='lite', local_mode=False, debug_mode=True)

    #print "Local: " + str(num_ripls) + " ripls"
    #mripl = venture.venturemagics.ip_parallel.MRipl(num_ripls, backend='lite', local_mode=True, debug_mode=True)

    print "******** loading program"

    mripl.assume("pose", "(list (uniform_continuous 0 1) (uniform_continuous 0 1) (uniform_continuous 0 6.28))")
    mripl.assume("get_pose", "(lambda (i) pose)")
    mripl.assume("slam_map", "(list (list 0.75 0.5))")

    mripl.observe("(simulate_laser pose slam_map 0.05 0.05)", gen_laser(laser))

    print "******** saving scenes"

    prior_scenes = mripl.map_proc(no_ripls='all', proc=read_scene, t=0)
    for i,init_scene in enumerate(prior_scenes):
        display(0, prefix="test_simple_prior_scene_%i" % i, scene=init_scene, true_map=true_map, true_pose=true_pose, verbose=False)

    print "******** starting inference"

    dt = 0
    t_prev = time.time()

    for i in range(1):
        print "starting block %i" % i
        mripl.infer("(mh default one 10)")
        dt = time.time() - t_prev
        t_prev = t_prev + dt
        print "took %d seconds" % dt

    print "******** finished inference"

    posterior_scenes = mripl.map_proc(no_ripls='all', proc=read_scene, t=0)

    print "******** obtained posterior scenes"

    print "pose: " + str(mripl.sample("(lookup pose 0)"))

    results = mripl.snapshot(exp_list=("(lookup pose 0)", "(lookup pose 1)"), scatter=True, plot=True, logscore=True)
    for i,fig in enumerate(results['figs']):
        fig.savefig("dump/test_%i.png" % i)
        del fig

    print "******** generated snapshot"

def render_laser(fig):
    print "FIXME: no laser rendering yet"

def test_diagnostics():
    import vehicle_simulator
    stub_sim = vehicle_simulator.create_vehicle_simulator("1_straight/data/noisy/", None, 0, None, None)
    gps_frame, control_frame, laser_frame, ground_frame = vehicle_simulator.read_frames("1_straight/data/noisy/", read_ground = True)
    MAX_FRAME = 10

    obstacles = vehicle_simulator.read_frame( dirname = "1_straight/", **dict(filename="obstacles.csv", colname_map=dict(GPSLat='y', GPSLon='x')) )
    true_map = []
    for i in range(len(obstacles)):
        row = obstacles.irow(i)
        true_map.append([row['x'], row['y']])
    print "**** TRUE MAP: " + str(true_map)    

    control_frame, gps_frame, laser_frame, ground_frame, dt_frame = vehicle_simulator.uniformize(control_frame, gps_frame, laser_frame, ground_frame, MAX_FRAME)

    true_poses = ground_frame

    stub_sim.plot(control_frame, gps_frame, laser_frame, ground_frame, dt_frame, max_frame = MAX_FRAME, 
                  poses_override = [ true_poses[i] for i in range(MAX_FRAME) ],
                  maps_override = [ true_map for i in range(MAX_FRAME) ] )

#import cProfile, pstats
#pr = cProfile.Profile()
#pr.enable()

test_diagnostics()
#test_intersection()
#test_simple()

#pr.disable()
#ps = pstats.Stats(pr).sort_stats('cumulative')
#ps.print_stats()

#run_test(ripl=make_lite_church_prime_ripl(), num_steps=3, num_infers=500)
