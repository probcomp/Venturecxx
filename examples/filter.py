import matplotlib
import pylab
import argparse
import os

import scene_plot_utils as spu
import vehicle_program as vp
import vehicle_simulator as vs

import numpy as np
import numpy.random as npr

from contexts import Timer


def read_combined_frame():
    base_dir = '/home/dlovell/Desktop/PPAML/CP1-Quad-Rotor/data/automobile/'
    parser = argparse.ArgumentParser()
    parser.add_argument('--base_dir', type=str, default=base_dir)
    parser.add_argument('--dataset_name', type=str, default='5_eight')
    parser.add_argument('--ground', action='store_true')
    args = parser.parse_args()
    base_dir = args.base_dir
    dataset_name = args.dataset_name
    use_noisy = not args.ground
    which_data = 'noisy' if use_noisy else 'ground'
    #
    
    
    gps_to_clean_gps = dict(GPSLat='clean_y', GPSLon='clean_x', Orientation='clean_heading')
    clean_gps_frame_config = dict(filename='slam_gps.csv', index_col='TimeGPS',
        colname_map=gps_to_clean_gps)
    
    dirname = os.path.join(base_dir, dataset_name, 'data', which_data)
    clean_dirname = os.path.join(base_dir, dataset_name, 'data', 'ground')
    gps_frame, control_frame, laser_frame, sensor_frame = vs.read_frames(dirname)
    clean_gps_frame = vs.read_frame(dirname=clean_dirname, **clean_gps_frame_config)

    combined_frame = vs.combine_frames(control_frame, gps_frame)
    slength = len(combined_frame['i'])
    empty = [np.nan for i in range(slength)]
    combined_frame['clean_x'] = empty
    combined_frame['clean_y'] = empty
    combined_frame['clean_heading'] = empty

#    import pdb
#    pdb.set_trace()
    
    for i in range(len(clean_gps_frame)):
      combined_frame.ix[clean_gps_frame.irow(i).name,'clean_x'] = clean_gps_frame.irow(i)['clean_x']
      combined_frame.ix[clean_gps_frame.irow(i).name,'clean_y'] = clean_gps_frame.irow(i)['clean_y']
      combined_frame.ix[clean_gps_frame.irow(i).name,'clean_heading'] = clean_gps_frame.irow(i)['clean_heading']
    
    for i in range(20):
      print str(combined_frame.irow(i))
#      print str(clean_gps_frame.irow(i))
      print "================================================"
          
    return combined_frame, clean_gps_frame, dataset_name
    
def plot_pose(figname, xlim, ylim, xs=None, ys=None, headings=None, clean_gps_pose=None):
    with Timer(figname) as t:
        if xs is None:
            xs = np.zeros((1,1))
            ys = np.zeros((1,1))
            headings = np.zeros((1,1))

        spu.plot_scene_scatter(xs, ys, headings, clean_gps_pose)
        pylab.gca().set_xlim(xlim)
        pylab.gca().set_ylim(ylim)
        pylab.savefig(figname)
        pylab.close()
        pass
    return

def get_clean_gps_poses(_is, combined_frame, clean_gps_frame):
    def get_clean_gps_pose(_ix):
        xs = clean_gps_frame.ix[_ix]
        return (xs.x, xs.y, xs.heading)
    i_to_ix = dict(zip(combined_frame.i, combined_frame.index))
    indices = map(i_to_ix.get, _is)
    clean_gps_poses = map(get_clean_gps_pose, indices)
    return clean_gps_poses

def get_lims(clean_gps_frame):
    min_xs = clean_gps_frame.min()
    max_xs = clean_gps_frame.max()
    min_x, max_x = min_xs.x, max_xs.x
    min_y, max_y = min_xs.y, max_xs.y
    delta_x = (max_x - min_x) * .05
    delta_y = (max_y - min_y) * .05
    delta_x = max(delta_x, .5)
    delta_y = max(delta_y, .5)
    xlim = (min_x - delta_x, max_x + delta_x)
    ylim = (min_y - delta_y, max_y + delta_y)
    return xlim, ylim  

print "Loading data"
combined_frame, clean_gps_frame, dataset_name = read_combined_frame()
#print "Aligning clean gps with combined_frame"
#clean_gps_poses = get_clean_gps_poses(range(len(combined_frame)), combined_frame, clean_gps_frame)

xlim = (-10, 10)
ylim = (-5, 5)
#xlim, ylim = get_lims(clean_gps_frame)
#zoom out so we can see in the case of inaccurate estimates
#ylim = (5 * ylim[0], 5 * ylim[1])

print "Set plot limits: " + str((xlim, ylim))

# goal 0: we understand input format
# goal 1: we generate poses + ground truth and see what's happening

# goal 2: we do inference with just noise written in native venture with fixed params and get best results

# goal 3: we make output compatible w dan stuff
# goal 4: dan submits that solution (no motion model)
#
# goal 5: we try to debug motion model, etc...

noisy_gps_stds = {}
noisy_gps_stds['x'] = 0.05
noisy_gps_stds['y'] = 0.05
noisy_gps_stds['heading'] = 0.01

import venture.shortcuts
ripl = venture.shortcuts.make_church_prime_ripl()

times = []
row_is = range(min(1000, len(combined_frame)))
gps_frame_count = 0

for row_i in row_is:
    with Timer('row %s' % row_i) as t:
        combined_frame_row = combined_frame.irow(row_i)

        clean_gps = (combined_frame_row['clean_x'], combined_frame_row['clean_y'], combined_frame_row['clean_heading'])
                
        #clean_gps = (clean_gps_poses[0][row_i], clean_gps_poses[1][row_i], clean_gps_poses[2][row_i])
        #clean_gps_row = clean_gps_poses.irow(row_i)
        #clean_gps = (clean_gps_row['x'], clean_gps_row['y'], clean_gps_row['heading'])
        
        print "------"
        print "combined frame %d: \n" % row_i + str(combined_frame_row)
        print "clean gps: \n" + str(clean_gps)

        xs = []
        ys = []
        headings = []
        
        # FIXME: parameterize number of samples
        for k in range(1):
            ripl.clear()
            
            # FIXME: easy accuracy win by using estimates from last state with noisy gps as a prior
            if row_i is 0:
              ripl.assume("x", "(normal 0 1)")
              ripl.assume("y", "(normal 0 1)")
              ripl.assume("heading", "(uniform_continuous -3.14 3.14)")
            else:
              ripl.assume("x", "(normal %f 0.1)" % prev_x)
              ripl.assume("y", "(normal %f 0.1)" % prev_y)
              ripl.assume("heading", "(normal %f 0.1)" % prev_heading)
              
            if not np.isnan(combined_frame_row['x']):
                noisy_gps_x = combined_frame_row['x']
                noisy_gps_y = combined_frame_row['y']
                noisy_gps_heading = combined_frame_row['heading']
              
                print "NOISY: " + str((noisy_gps_x, noisy_gps_y, noisy_gps_heading))
                
                ripl.observe("(normal x %f)" % noisy_gps_stds['x'], noisy_gps_x)
                ripl.observe("(normal y %f)" % noisy_gps_stds['y'], noisy_gps_y)
                #ripl.observe("(normal heading %f)" % noisy_gps_stds['heading'], noisy_gps_heading)
            
            ripl.infer("(incorporate)")
            ripl.infer("(slice default one 20)")
            
            xs.append(float(ripl.sample("x")))
            ys.append(float(ripl.sample("y")))
            headings.append(float(ripl.sample("heading")))
                          
        xs = np.array(xs)
        ys = np.array(ys)
        headings = np.array(headings)

        prev_x = xs.mean()
        prev_y = ys.mean()
        prev_heading = headings.mean()

        print "PREVIOUS HEADING: " + str((prev_x, prev_y, prev_heading))
                
        print "xs: " + str(xs)
        print "ys: " + str(ys)
        print "headings: " + str(headings)

        if not np.isnan(combined_frame_row['x']):
          gps_frame_count += 1
          plot_pose(dataset_name + "_raw_%s.png" % gps_frame_count, xlim, ylim, xs=xs, ys=ys, headings=headings, clean_gps_pose=clean_gps)
    times.append(t.elapsed)
    pass
print 'all rows took %d seconds (%s per timestep)' % (sum(times), sum(times) / len(times))

mp4_name = dataset_name + '.mp4'
template_str = dataset_name + '_raw_%1d.png'
os.system('avconv -y -r 5 -b 1800 -i %s %s' % (template_str, mp4_name))

