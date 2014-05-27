import operator
import functools

import pylab
import numpy as np

from venture.venturemagics.ip_parallel import MRipl

# FIXME dirty hack; directory layout implications
import examples.vehicle_simulator

class Simulator(object):
    # where to run diagnostics?
    def __init__(self, program, observe_strs_list, sample_strs_list,
            N_ripls, backend, N_infer):
        self.observe_strs_list = observe_strs_list
        self.sample_strs_list = sample_strs_list
        self.next_i = 0
        self.N_infer = N_infer
        self.program = program

        self.N_ripls = N_ripls
        
        if N_ripls > 0:
            self.mripl = MRipl(N_ripls, backend=backend)
            self.mripl.execute_program(self.program)
        

    def step(self, N_infer=None):
        N_infer = first_non_none(N_infer, self.N_infer)
        observe_strs, sample_strs = self._get_next_observe_and_sample_str()
        self._observe(observe_strs)
        self._infer(N_infer)
        samples = self._sample(sample_strs)
        return samples

    def _get_next_observe_and_sample_str(self):
        observe_str = self.observe_strs_list[self.next_i]
        sample_str = self.sample_strs_list[self.next_i]
        self.next_i += 1
        return observe_str, sample_str

    def _observe(self, observe_strs):
        print 'observing: %s' % observe_strs
        _observe_datum = functools.partial(observe_datum, self.mripl)
        return map(_observe_datum, observe_strs)

    def _infer(self, N_infer):
        hypers = '(mh hypers one %s)' % N_infer
        state = '(mh state all %s)' % N_infer
        #
        print "infering: %s" % hypers
        self.mripl.infer(hypers)
        print "done infering: %s" % hypers
        #
        print "infering: %s" % state
        self.mripl.infer(state)
        print "done infering: %s" % state
        # self.mripl.infer(N_infer)
        pass

    def _sample(self, sample_strs):
        munge_sample = lambda sample: reduce(operator.add, zip(*sample))
        print 'sampling: %s' % sample_strs
        raw_samples = map(self.mripl.sample, sample_strs)
        samples = map(munge_sample, raw_samples)
        return samples

    def _plot_scene(self, particle_ids, poses_seqs, maps_seqs, dead_reckon_seq, gps_seq, ground_seq, bright=False):
        
        pose_color = 1.0 if bright else 0.2

        if self.N_ripls > 0:
            for m in particle_ids:
                # add the pose history for this "particle"
                pylab.plot([poses[m][0] for poses in poses_seqs], [poses[m][1] for poses in poses_seqs], '-x', color='r', alpha=0.2)
                
                # add the map history for this "particle"
                pylab.plot([slam_maps[m][l][0] for l in slam_maps[m] for slam_maps in maps_seqs], [slam_maps[m][l][1] for l in slam_maps[m] for slam_maps in maps_seqs], '-o', color='b', alpha=0.2)
                
        # FIXME: add orientations to ground truth, pose, dead reckoning

        # add the dead reckoning history
        pylab.plot([dead_reckon[0] for dead_reckon in dead_reckon_seq], [dead_reckon[1] for dead_reckon in dead_reckon_seq], '-x', color='g', alpha=0.2)
            
        # add the gps history
        pylab.plot([gps[0] for gps in gps_seq if gps is not None], [gps[1] for gps in gps_seq if gps is not None], '-o', color='magenta', alpha=0.2)

        # add the ground truth history
        pylab.plot([ground[0] for ground in ground_seq if ground is not None], [ground[1] for ground in ground_seq if ground is not None], '-x', color='black', alpha=0.2)

        pylab.xlim([-30, 30])
        pylab.ylim([-30, 30])

    def plot(self, control_frame, gps_frame, laser_frame, ground_frame, dt_frame, max_frame = 2, subset_frames = None, plot_laser_frames = None, poses_override = None, maps_override = None):
        # FIXME: Draw ground truth map in, also

        # put these in a format where they're all aligned

        if subset_frames is None:
            subset_frames = range(len(control_frame))

        if plot_laser_frames is None:
            plot_laser_frames = subset_frames
        else:
            for i in plot_laser_frames:
                assert i in subset_frames, "ERROR: plot_laser_frames must be subset of subset_frames"

        # now we have subset frames and plot_laser_frames

        poses_seqs = [[] for i in range(self.N_ripls)]
        maps_seqs  = [[] for i in range(self.N_ripls)]
        ground_seq = []
        control_seq = []
        dead_reckon_seq = []
        gps_seq = []
        laser_seq = []

        # FIXME: display obstacles (true maps?) or already displayed? need test cases to check different kinds of plots and use caes

        # FIXME: units may not agree between real problem and current --- or be different for different coordinates

        def plot_laser(ground, laser, real=True):
            print "...plotting laser values"
            #print "- ground: " + str(ground)
            #print "- laser at plotting: " + str(laser[:5])

            if real:
                color = 'k'
            else:
                color = 'g'

            step_theta = 2 * np.pi / 361
            #print "step_theta: " + str(step_theta)
            for i, reading in enumerate(laser):
                range_val, intensity_val = reading
                #print "reading: " + str(reading)
                
                theta = i * step_theta
                laser_heading = ground[2] + theta
                step_x = np.cos(laser_heading) * range_val
                step_y = np.sin(laser_heading) * range_val
                start_x = ground[0]
                start_y = ground[1]
                end_x = ground[0] + step_x
                end_y = ground[1] + step_y

                #print "(theta, step_x, step_y): " + str((theta, step_x, step_y))
                #print "(start_x, start_y, end_x, end_y): " + str((start_x, start_y, end_x, end_y))


                pylab.plot([start_x, end_x], [start_y, end_y], color='k', linestyle='-', alpha=0.1) #FIXME represent intensities; also check error model for sensors and parameter inference

        for f in range(max_frame):
            print "Processing frame " + str(f)

            # grab the new data from the mripls
            # append to paths so far
            if self.N_ripls > 0:
                poses = self.mripl.sample("(get_pose %i)" % f)
                maps  = self.mripl.sample("slam_map")
            else:
                if poses_override is None:
                    poses = None
                else:
                    poses = poses_override[f]

                if maps_override is None:
                    maps = None
                else:
                    maps = maps_override[f]

            ground = ground_frame[f]
            control = control_frame[f]
            laser = laser_frame[f]

            if f == 0:
                # for first frame, hackily initialize dead reckoning
                dead_reckon = [0, 0, 0]
            else:
                # for all other frames, linearly interpolate from the past

                dt = dt_frame[f]
                theta = dead_reckon_seq[-1][2] #heading in absolute radians
                x = dead_reckon_seq[-1][0]
                y = dead_reckon_seq[-1][1]
                theta_dot = control[1]
                velocity = control[0]

                dtheta = theta_dot * dt
                theta_prime = dtheta + theta

                dy = np.sin(theta) * velocity * dt
                dx = np.cos(theta) * velocity * dt

                x_prime = x + dx
                y_prime = y + dy

                dead_reckon = [x_prime, y_prime, theta_prime]

            gps = gps_frame[f]

            poses_seqs.append(poses)
            maps_seqs.append(maps)
            ground_seq.append(ground)
            control_seq.append(control)
            dead_reckon_seq.append(dead_reckon)
            gps_seq.append(gps)
            laser_seq.append(laser)

            # for each subset frame:
            if f in subset_frames:

                if self.N_ripls > 0:
                    pylab.figure()
                    self._plot_scene(range(self.N_ripls), poses_seqs, maps_seqs, dead_reckon_seq, gps_seq, ground_seq)
                    pylab.savefig('dump/last_belief_%05i.png' % f)

                if self.N_ripls == 0:
                    # no inference, but still can show what the lasers look like, and key simulated lasers on
                    # a special map and pose argument

                    if poses is not None and maps is not None:
                        # user wants to draw the map and the data
                        #print "DATA: " + str(f)

                        if laser is not None and f in plot_laser_frames:
                            print " = real laser data plotting"
                            fig = pylab.figure()
                            self._plot_scene([0], poses, maps, dead_reckon_seq, gps_seq, ground_seq, bright=True)
                            plot_laser(ground, laser, real=True)
                            pylab.savefig('dump/last_data_%05i.png' % f)
                            pylab.close(fig)

                            print " = anticipated laser data plotting"
                            fig = pylab.figure()
                            self._plot_scene([0], poses, maps, dead_reckon_seq, gps_seq, ground_seq, bright=True)
                            sim_laser_data = examples.vehicle_simulator.raw_simulate_laser(poses, maps) # FIXME inaccurate representation of noise, will be misleading...
                            plot_laser(poses, sim_laser_data, real=False)
                            pylab.savefig('dump/last_dsim_%05i.png' % f)
                            pylab.close(fig)

                for m in range(self.N_ripls):
                    # plot the raw frame (integrated control, ground gps, noisy gps, current pose) 

                    fig = pylab.figure()
                    self._plot_scene([m], poses_seqs, maps_seqs, dead_reckon_seq, gps_seq, ground_seq)
                    pylab.savefig('dump/last_state_%05i_%05i.png' % (f, m))
                    pylab.close(fig)

                    if f in plot_laser_frames:
                        # if we are plotting the laser for this frame:
                        print " plotting anticipated laser data for frame and particle " + str((f, m))
                        fig = pylab.figure()
                        self._plot_scene([m], poses_seqs, maps_seqs, dead_reckon_seq, gps_seq, ground_seq, bright=True)
                        sim_laser_data = examples.vehicle_simulator.raw_simulate_laser(poses[m], maps[m]) # FIXME inaccurate representation of noise, will be misleading...
                        plot_laser(poses, sim_laser_data, real=False)
                        pylab.savefig('dump/last_laser_%05i_%05i.png' % (f, m))
                        pylab.close(fig)


def printif(boolean, to_print):
    if boolean:
        print to_print
        pass
    return

def observe_datum(ripl, (observe_str, value), verbose=False):
    print_str = "ripl.observe(%s, %s)" % (observe_str, value)
    printif(verbose, print_str)
    return ripl.observe(observe_str, value)

def first_non_none(*args):
    my_or = lambda x, y: x if x is not None else y
    return reduce(my_or, args)
