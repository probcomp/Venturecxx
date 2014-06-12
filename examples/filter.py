import matplotlib
matplotlib.use("Agg")
import pylab
import argparse
import os

import scene_plot_utils as spu
import vehicle_simulator as vs

import numpy as np
import numpy.random as npr

from contexts import Timer

parser = argparse.ArgumentParser()
parser.add_argument('input_dir', type=str)
parser.add_argument('output_dir', type=str)
parser.add_argument('--max_time', type=float, default=None)
parser.add_argument('--clean_dir', type=str, default=None)
parser.add_argument('--dataset_name', type=str, default='')
parser.add_argument('--ground', action='store_true')
parser.add_argument('--version', default='random_walk')
parser.add_argument('--plot', action='store_true')
parser.add_argument('--frames', type=int, default=100000)
parser.add_argument('--samples', type=int, default=10)
args = parser.parse_args()

# Read and pre-process the data.
def read_combined_frame():
    dataset_name = args.dataset_name
    use_noisy = not args.ground
    which_data = 'noisy' if use_noisy else 'ground'
    
    gps_to_clean_gps = dict(GPSLat='clean_y', GPSLon='clean_x', Orientation='clean_heading')
    clean_gps_frame_config = dict(filename='slam_gps.csv', index_col='TimeGPS',
        colname_map=gps_to_clean_gps)
    
    gps_frame, control_frame, laser_frame, sensor_frame = vs.read_frames(args.input_dir)
    combined_frame = vs.combine_frames(control_frame, gps_frame)
    slength = len(combined_frame['i'])
    empty = [np.nan for i in range(slength)]
    combined_frame['clean_x'] = empty
    combined_frame['clean_y'] = empty
    combined_frame['clean_heading'] = empty
    if args.max_time is not None:
        combined_frame = combined_frame[combined_frame.index < args.max_time]
    
    clean_gps_frame = None
    if args.clean_dir is not None:
        clean_gps_frame = vs.read_frame(dirname=args.clean_dir, **clean_gps_frame_config)
        for i in range(len(clean_gps_frame)):
            combined_frame.ix[clean_gps_frame.irow(i).name,'clean_x'] = clean_gps_frame.irow(i)['clean_x']
            combined_frame.ix[clean_gps_frame.irow(i).name,'clean_y'] = clean_gps_frame.irow(i)['clean_y']
            combined_frame.ix[clean_gps_frame.irow(i).name,'clean_heading'] = clean_gps_frame.irow(i)['clean_heading']
    return combined_frame, clean_gps_frame, dataset_name

# Plot samples along with the ground truth.
def plot_pose(figname, xlim, ylim, xs=None, ys=None, headings=None, clean_gps_pose=None):
    with Timer(figname) as t:
        spu.plot_scene_scatter(xs, ys, headings, clean_gps_pose)
        pylab.gca().set_xlim(xlim)
        pylab.gca().set_ylim(ylim)
        pylab.savefig(figname)
        pylab.close()
        pass
    return

print "Loading data"
combined_frame, clean_gps_frame, dataset_name = read_combined_frame()

xlim = (-10, 10)
ylim = (-5, 5)
#xlim, ylim = get_lims(clean_gps_frame)

print "Set plot limits: " + str((xlim, ylim))

out_cols = ['SLAMGPSTime', 'SLAMLat', 'SLAMLon']

class RandomWalkStepper(object):
    def __init__(self):
        # Parameters for the random walk prior with Gaussian steps.
        self.noisy_gps_stds = dict(x=0.05, y=0.05, heading=0.01)
        self.N_samples = args.samples
        print "Generating %d samples per time step" % self.N_samples


    def frame(self, ripl, row_i, combined_frame_row):

        xs = []
        ys = []
        headings = []

        # generate the samples
        for k in range(self.N_samples):
            ripl.clear()

            if row_i is 0:
              ripl.assume("x", "(normal 0 1)")
              ripl.assume("y", "(normal 0 1)")
              ripl.assume("heading", "(uniform_continuous -3.14 3.14)")
            else:
              ripl.assume("x", "(normal %f 0.1)" % self.prev_x)
              ripl.assume("y", "(normal %f 0.1)" % self.prev_y)
              ripl.assume("heading", "(normal %f 0.1)" % self.prev_heading)

            # we have noisy gps observations, let's condition on them!
            if not np.isnan(combined_frame_row['x']):
                noisy_gps_x = combined_frame_row['x']
                noisy_gps_y = combined_frame_row['y']
                noisy_gps_heading = combined_frame_row['heading']

                #print "NOISY: " + str((noisy_gps_x, noisy_gps_y, noisy_gps_heading))

                ripl.observe("(normal x %f)" % self.noisy_gps_stds['x'], noisy_gps_x)
                ripl.observe("(normal y %f)" % self.noisy_gps_stds['y'], noisy_gps_y)
                #ripl.observe("(normal heading %f)" % self.noisy_gps_stds['heading'], noisy_gps_heading)

                ripl.infer("(slice default one 20)")

            xs.append(float(ripl.sample("x")))
            ys.append(float(ripl.sample("y")))
            headings.append(float(ripl.sample("heading")))

        xs = np.array(xs)
        ys = np.array(ys)
        headings = np.array(headings)

        self.prev_x = xs.mean()
        self.prev_y = ys.mean()
        self.prev_heading = headings.mean()

        #print "PREVIOUS HEADING: " + str((self.prev_x, self.prev_y, self.prev_heading))

        #print "xs: " + str(xs)
        #print "ys: " + str(ys)
        #print "headings: " + str(headings)
        return (xs, ys, headings)

def _rotate(lst):
    item = lst[0]
    del lst[0]
    lst.append(item)

def _sample_rotating_distinguished_particle(ripl, exp):
    # Oh, what a hack...
    engine = ripl.sivm.core_sivm.engine
    _rotate(engine.traces)
    _rotate(engine.weights)
    return ripl.sample(exp)

def _sample_from_all_particles(ripl, exp):
    return [_sample_rotating_distinguished_particle(ripl, exp) for _ in range(len(ripl.sivm.core_sivm.engine.traces))]

class RandomWalkParticleFilter(object):
    def __init__(self, particles=1):
        self.window = 1
        self.particles = particles
        print "Particle filtering with %d particles and window of size %d" % (self.particles, self.window)
        self.noisy_gps_stds = dict(x=0.05, y=0.05, heading=0.01)
        self.obs_at = {}

    def frame(self, ripl, row_i, combined_frame_row):
        self.assume(ripl, row_i, combined_frame_row)
        self.observe(ripl, row_i, combined_frame_row)
        self.infer(ripl, row_i)
        self.forget(ripl, row_i, combined_frame_row)

        return (np.array(_sample_from_all_particles(ripl, "x_%d" % row_i)),
                np.array(_sample_from_all_particles(ripl, "y_%d" % row_i)),
                np.array(_sample_from_all_particles(ripl, "heading_%d" % row_i)))

    def assume(self, ripl, row_i, _combined_frame_row):
        if row_i is 0:
          ripl.infer("(resample %d)" % self.particles)
          ripl.assume("x_%d" % row_i, "(normal 0 1)", label="x_%d" % row_i)
          ripl.assume("y_%d" % row_i, "(normal 0 1)", label="y_%d" % row_i)
          ripl.assume("heading_%d" % row_i, "(uniform_continuous -3.14 3.14)", label="heading_%d" % row_i)
        else:
          ripl.assume("x_%d" % row_i, "(normal x_%d 0.1)" % (row_i-1), label="x_%d" % row_i)
          ripl.assume("y_%d" % row_i, "(normal y_%d 0.1)" % (row_i-1), label="y_%d" % row_i)
          ripl.assume("heading_%d" % row_i, "(normal heading_%d 0.1)" % (row_i-1), label="heading_%d" % row_i)

    def observe(self, ripl, row_i, combined_frame_row):
        # we have noisy gps observations, let's condition on them!
        if not np.isnan(combined_frame_row['x']):
            self.obs_at[row_i] = True
            noisy_gps_x = combined_frame_row['x']
            noisy_gps_y = combined_frame_row['y']
            noisy_gps_heading = combined_frame_row['heading']

            #print "NOISY: " + str((noisy_gps_x, noisy_gps_y, noisy_gps_heading))

            ripl.observe("(normal x_%d %f)" % (row_i, self.noisy_gps_stds['x']), noisy_gps_x, label="obs_x_%d" % row_i)
            ripl.observe("(normal y_%d %f)" % (row_i, self.noisy_gps_stds['y']), noisy_gps_y, label="obs_y_%d" % row_i)

    def infer(self, ripl, _row_i):
        ripl.infer("(resample %d)" % self.particles)
        ripl.infer("(slice default one 20)")

    def forget(self, ripl, row_i, _combined_frame_row):
        if row_i >= self.window:
            ripl.freeze("x_%d" % (row_i - self.window))
            ripl.freeze("y_%d" % (row_i - self.window))
            ripl.freeze("heading_%d" % (row_i - self.window))
            if (row_i - self.window) in self.obs_at:
                ripl.forget("obs_x_%d" % (row_i - self.window))
                ripl.forget("obs_y_%d" % (row_i - self.window))
        if row_i > self.window:
            ripl.forget("x_%d" % (row_i - self.window - 1))
            ripl.forget("y_%d" % (row_i - self.window - 1))
            ripl.forget("heading_%d" % (row_i - self.window - 1))

class MotionModelParticleFilter(RandomWalkParticleFilter):
    def __init__(self, particles=1):
        super(MotionModelParticleFilter, self).__init__(particles)
        self.window = 2
        self.last_vel = "(normal 0 1)"
        self.last_steer = "(normal 0 1)"
        self.noisy_motion_stds = dict(x = 0.03, y = 0.03, heading = 0.01)

    def assume(self, ripl, row_i, combined_frame_row):
        if not np.isnan(combined_frame_row['Velocity']):
            # If no control is given, model it as the same as the
            # last frame where there was one.
            self.last_vel = combined_frame_row['Velocity']
        if not np.isnan(combined_frame_row['Steering']):
            self.last_steer = combined_frame_row['Steering']

        if row_i is 0:
          ripl.infer("(resample %d)" % self.particles)
          ripl.assume("dt_%d" % row_i, 0, label="dt_%d" % row_i)
          ripl.assume("offset_%d" % row_i, 0, label="offset_%d" % row_i)
          ripl.assume("x_%d" % row_i, "(normal 0 10)", label="x_%d" % row_i)
          ripl.assume("y_%d" % row_i, "(normal 0 10)", label="y_%d" % row_i)
          ripl.assume("heading_%d" % row_i, "(uniform_continuous -3.14 3.14)", label="heading_%d" % row_i)
        else:
          ripl.assume("dt_%d" % row_i, combined_frame_row['dt'], label="dt_%d" % row_i)
          ripl.assume("heading_%d" % row_i,
                      "(normal (+ heading_%d (* dt_%d %s)) %f)" % (row_i-1, row_i, self.last_steer, self.noisy_motion_stds['heading']),
                      label="heading_%d" % row_i)
          ripl.assume("offset_%d" % row_i,
                      "(* dt_%d %s)" % (row_i, self.last_vel),
                      label="offset_%d" % row_i)
          ripl.assume("x_%d" % row_i,
                      "(normal (+ x_%d (* offset_%d (cos heading_%d))) %f)" % (row_i-1, row_i, row_i, self.noisy_motion_stds['x']),
                      label="x_%d" % row_i)
          ripl.assume("y_%d" % row_i,
                      "(normal (+ y_%d (* offset_%d (sin heading_%d))) %f)" % (row_i-1, row_i, row_i, self.noisy_motion_stds['y']),
                      label="y_%d" % row_i)

    def forget(self, ripl, row_i, combined_frame_row):
        super(MotionModelParticleFilter, self).forget(ripl, row_i, combined_frame_row)
        # Don't need to (and can't) freeze dt and offset, because they are deterministic
        if row_i > self.window:
            ripl.forget("offset_%d" % (row_i - self.window - 1))
            ripl.forget("dt_%d" % (row_i - self.window - 1))

    def infer(self, ripl, row_i):
        ripl.infer("(resample %d)" % self.particles)
        ripl.infer("(mh default one %d)" % (30 * self.window))
        if row_i < self.window:
            # Work hard on the beginning, because the prior is likely to be bad
            # and we don't want to seed the motion model poorly
            # ripl.infer("(mh default one 950)")
            ripl.infer("(slice default one %d)" % (10 * self.window))

# Run the solution
def runSolution(method):

  import venture.shortcuts
  ripl = venture.shortcuts.make_church_prime_ripl()

  row_num = min(args.frames, len(combined_frame))
  print "Using %d rows" % row_num
  row_is = range(row_num)

  gps_frame_count = 0

  times = []

  out_rows = []

  # For each row...
  for row_i in row_is:
      with Timer('row %s' % row_i) as t:
          combined_frame_row = combined_frame.irow(row_i)

          clean_gps = (combined_frame_row['clean_x'], combined_frame_row['clean_y'], combined_frame_row['clean_heading'])

          #print "------"
          #print "combined frame %d: \n" % row_i + str(combined_frame_row)
          #print "clean gps: \n" + str(clean_gps)

          (xs, ys, headings) = method.frame(ripl, row_i, combined_frame_row)

          # if the frame has gps signal, plot it
          if not np.isnan(combined_frame_row['x']):
              gps_frame_count += 1
              if args.plot:
                plot_pose(dataset_name + "_raw_%s.png" % gps_frame_count, xlim, ylim, xs=xs, ys=ys, headings=headings, clean_gps_pose=clean_gps)
              out_rows.append((combined_frame_row.name, np.average(ys), np.average(xs)))
      
      times.append(t.elapsed)

  print 'all rows took %d seconds (%s per timestep)' % (sum(times), sum(times) / len(times))
  
  if args.plot:
    # Make the mp4 movie.
    mp4_name = dataset_name + '.mp4'
    template_str = dataset_name + '_raw_%1d.png'
    os.system('avconv -y -r 5 -b 1800 -i %s %s' % (template_str, mp4_name))
  
  return out_rows


approaches = dict(random_walk = RandomWalkStepper(),
                  one_particle = RandomWalkParticleFilter(1),
                  particle_filter = RandomWalkParticleFilter(10),
                  motion_model_base = MotionModelParticleFilter(1))
approach = approaches[args.version]

def ensure(path):
  path = path[:path.rfind('/')]
  if not os.path.exists(path):
    os.makedirs(path)

def writeCSV(filename, cols, rows):
  with open(filename, 'w') as f:
    f.write(','.join(cols) + '\n')
    for row in rows:
      f.write(','.join(map(str, row)) + '\n')

out_rows = runSolution(approach)
out_file = '%s/slam_out_path.csv' % args.output_dir
ensure(out_file)
writeCSV(out_file, out_cols, out_rows)

print "Wrote output to " + out_file

landmarks_cols = ['SLAMBeaconX','SLAMBeaconY']
landmarks_rows = [(0, 0)]
landmarks_file = '%s/slam_out_landmarks.csv' % args.output_dir
writeCSV(landmarks_file, landmarks_cols, landmarks_rows)

print "Wrote landmarks to " + landmarks_file

