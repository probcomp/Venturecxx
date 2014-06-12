import matplotlib
matplotlib.use('Agg')
#

import os,time
import sys,subprocess
import argparse
import numpy as np
import numpy.random as npr
from matplotlib import pyplot as plt
from IPython.core.debugger import Pdb
#
import venture.shortcuts
import scene_plot_utils as spu
import vehicle_simulator as vs
from contexts import Timer
from venture.venturemagics.ip_parallel import display_directives


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('frames',type=int)
    parser.add_argument('per_block',type=int)
    parser.add_argument('plot',type=bool)
    cl_args = parser.parse_args()
    return cl_args

def set_trace():
    Pdb(color_scheme='LightBG').set_trace(sys._getframe().f_back)

# Read and pre-process the data.
def read_combined_frame():
    gps_frame, control_frame, laser_frame, sensor_frame = vs.read_frames(args.input_dir)
    combined_frame = vs.combine_frames(control_frame, gps_frame)

    clean_gps_frame = None
    if args.clean_dir is not None:
        gps_to_clean_gps = dict(GPSLat='clean_y', GPSLon='clean_x', Orientation='clean_heading')
        clean_gps_frame_config = dict(filename='slam_gps.csv', index_col='TimeGPS',
            colname_map=gps_to_clean_gps)
        clean_gps_frame = vs.read_frame(dirname=args.clean_dir, **clean_gps_frame_config)
        combined_frame = combined_frame.join(clean_gps_frame)

    if args.max_time is not None:
        combined_frame = combined_frame.truncate(after=args.max_time)
        clean_gps_frame = clean_gps_frame.truncate(after=args.max_time)

    combined_frame = combined_frame.head(args.frames)
    clean_gps_frame = clean_gps_frame.head(args.frames)

    return combined_frame, clean_gps_frame

# Plot samples along with the ground truth.
def plot_pose(figname, xlim, ylim, xs=None, ys=None, headings=None, clean_gps_pose=None):
    spu.plot_scene_scatter(xs, ys, headings, clean_gps_pose)
    plt.xlim(xlim)
    plt.ylim(ylim)
    plt.savefig(figname, format = 'png')
    plt.close()
    pass
    return

def make_movie(dataset_name, dirname=''):
# Make the mp4 movie.
    return
    mp4_name = os.path.join(dirname, dataset_name + '.mp4')
    template_str = os.path.join(dirname, dataset_name + '_raw_%1d.png')
    os.system('avconv -y -r 15 -i %s %s' % (template_str, mp4_name))
    return


def ensure(path):
    path = path[:path.rfind('/')]
    if not os.path.exists(path):
        os.makedirs(path)

def writeCSV(filename, cols, rows):
    with open(filename, 'w') as f:
        f.write(','.join(cols) + '\n')
        for row in rows:
            f.write(','.join(map(str, row)) + '\n')

def get_clean_gps(row):
    return (row['clean_x'], row['clean_y'], row['clean_heading'])

# Run the simple random walk solution.
def runRandomWalk():
    print 'runRandomWalk\n\n'

    # Parameters for the random walk prior with Gaussian steps.
    noisy_gps_stds = dict(x=0.05, y=0.05, heading=0.01)

    ripl = venture.shortcuts.make_church_prime_ripl()
    ripl.set_seed(1)
    
    print "Using %d row" % len(combined_frame)
    N_samples = args.samples
    print "Generating %d samples per time step" % N_samples

    times = []
    out_rows = []
    gps_frame_count = 0

  # For each row...
  
    for row_i, (_T, combined_frame_row) in enumerate(combined_frame.iterrows()):
        
        # set_trace()
        clean_gps = get_clean_gps(combined_frame_row)

        xs = []
        ys = []
        headings = []

        # generate the samples
        for k in range(N_samples):
            ripl.clear()

            if row_i is 0:
                ripl.assume("x", "(normal -6.1 1)")
                ripl.assume("y", "(normal -0.05 1)")
                ripl.assume("heading", "(uniform_continuous -3.14 3.14)")
            else:
                ripl.assume("x", "(normal %f 0.1)" % prev_x)
                ripl.assume("y", "(normal %f 0.1)" % prev_y)
                ripl.assume("heading", "(normal %f 0.1)" % prev_heading)

            if not np.isnan(combined_frame_row['x']):
                noisy_gps_x = combined_frame_row['x']
                noisy_gps_y = combined_frame_row['y']
                noisy_gps_heading = combined_frame_row['heading']

                ripl.observe("(normal x %f)" % noisy_gps_stds['x'], noisy_gps_x)
                ripl.observe("(normal y %f)" % noisy_gps_stds['y'], noisy_gps_y)
                #ripl.observe("(normal heading %f)" % noisy_gps_stds['heading'], noisy_gps_heading)

                ripl.infer("(mh default one 20)")
                #ripl.infer("(slice default one 20)")

            xs.append(float(ripl.sample("x")))
            ys.append(float(ripl.sample("y")))
            headings.append(float(ripl.sample("heading")))

        xs = np.array(xs)
        ys = np.array(ys)
        headings = np.array(headings)
        prev_x = xs.mean()
        prev_y = ys.mean()
        prev_heading = headings.mean()

        # if the frame has gps signal, plot it
        if not np.isnan(combined_frame_row['x']):
            gps_frame_count += 1
            if args.plot:
                st = '0' if gps_frame_count < 10 else ''
                filename = dataset_name + "_raw_%s.png" % (st+str(gps_frame_count))
                print filename
                plot_pose(filename, xlim, ylim, xs=xs, ys=ys,
                        headings=headings, clean_gps_pose=clean_gps)
            out_rows.append((combined_frame_row.name, np.average(xs), np.average(ys)))
        #times.append(t.elapsed)
    #print 'all rows took %d seconds (%s per timestep)' % (sum(times), sum(times) / len(times))
  
    if args.plot:
        make_movie(dataset_name,args.output_dir)
    return out_rows


def runApproach2():

    noisy_gps_stds = dict(heading=0.01)
    r = venture.shortcuts.make_church_prime_ripl()

    # setup particle filter
    freeze_on = args.freeze_on
    if args.particle:
        num_particles = args.num_particles
        r.infer('(resample %s)'%num_particles)

    print "Using %d row" % len(combined_frame)
    
    k = args.window_size
    times = []
    out_rows = []
    gps = []
    all_clean_gps = []
    gps_frame_count = 0


    # inference programs
    def mh_infer(T):
        Ts = range(T+1)[-k:]
        inf_str= lambda s:'(mh %i one %i)'%(s,args.per_block)
        forwards = [inf_str(t) for t in Ts]
        backwards = forwards[::-1]
        for _ in range(2):
            [r.infer(inf_str) for inf_str in backwards]
            [r.infer(inf_str) for inf_str in forwards]

        start = time.time()
        if np.mod(len(out_rows),10) == 0:
            lim = args.lim_parameters
            max_steps = 10
            steps = 1 + max_steps*( T*(-1./lim) +1 )
            r.infer('(mh parameters one %i)'% max(0,int(steps)) )
            if args.verbose:
                print (T,time.time() - start)
                print ' '.join(backwards)

    def particle_infer():
        r.infer('(resample %s)' % num_particles)


    def do_inference(T):
        if args.particle:
            particle_infer()
        else:
            mh_infer(T)

            
    # loop over times (no repeated samples)
    for T, (_T, combined_frame_row) in enumerate(combined_frame.iterrows()):
        clean_gps = get_clean_gps(combined_frame_row)
        xs = []
        ys = []
        headings = []
        x_datas = []
        y_datas = []

        was_gps_row = not np.isnan(combined_frame.irow((T-k)-1)['x'])
        is_gps_row = not np.isnan(combined_frame_row['x'])
        
        if T is 0:
            r.assume("x0", "(scope_include 0 0 (normal -6.1 1))", label="lx0")
            r.assume("y0", "(scope_include 0 1 (normal -.05 1))", label="ly0")
            r.assume("noisy_gps_x_std",
                     "(scope_include (quote parameters) 0 (gamma 1 10))")
            r.assume("noisy_gps_y_std",
                     "(scope_include (quote parameters) 1 (gamma 1 10))")
            r.assume("heading0", "(uniform_continuous -3.14 3.14)","lh0")

        else:
            r.assume("x%i"%T,
                     "(scope_include %i 0 (normal x%i 0.06))"%(T,T-1),"lx%i"%T)
            r.assume("y%i"%T,
                    "(scope_include %i 1 (normal y%i 0.001))"%(T,T-1),"ly%i"%T)
            r.assume("heading%i"%T, "(normal heading%i 0.1)" % (T-1),"lh%i"%T)
            
        
        if freeze_on and T > k:
            r.freeze("lx%i"%((T-k)-1))
            r.freeze("ly%i"%((T-k)-1))
            if was_gps_row:
                r.forget("x_data%i"%((T-k)-1))
                r.forget("y_data%i"%((T-k)-1))
        
        if is_gps_row:
            noisy_gps_x = combined_frame_row['x']
            noisy_gps_y = combined_frame_row['y']
            noisy_gps_heading = combined_frame_row['heading']
            if args.verbose and np.mod(T,19)==0:
                print "T:%i,obs:%s"%( T,(noisy_gps_x,noisy_gps_y,noisy_gps_heading))
                map(lambda x:display_directives(r,x),('assume','observe') )
                
            r.observe("(normal x%i noisy_gps_x_std)"%T, noisy_gps_x, label="x_data%i"%T )
            r.observe("(normal y%i noisy_gps_y_std)"%T, noisy_gps_y, label="y_data%i"%T)

            do_inference(T)
        
            store=lambda s:np.array(float(r.sample(s)))
            xs = store("x%i"%T)
            ys = store("y%i"%T)
            headings = store("heading%i"%T)
            gps_xs = store("noisy_gps_x_std")
            gps_ys = store("noisy_gps_y_std")

            if args.verbose:
                print '\n xs:',xs,'ys',ys,'\n','gps_x,y:',gps_xs,gps_ys,'\n'
                        
            if not np.isnan(combined_frame_row['x']):
                gps_frame_count += 1
                if args.plot:
                    st = '0' if gps_frame_count < 10 else ''
                    filename = dataset_name + "_raw_%s.png" % (st+str(gps_frame_count))
                    plot_pose(filename, xlim, ylim, xs=xs, ys=ys,
                              headings=headings, clean_gps_pose=clean_gps)
                out_rows.append((combined_frame_row.name, xs,ys))
                gps.append( (combined_frame_row.name,gps_xs,gps_ys) )
                all_clean_gps.append( (combined_frame_row.name,clean_gps) )

        elif args.always_infer:
            do_inference(T)
        else:
            pass


                
    if args.plot:
        make_movie(dataset_name,args.output_dir)

    round2 =  lambda t: np.round(t,2)
    all_clean = map( lambda p: (p[0],round2(p[1])), all_clean_gps )
    map2 = lambda l: map( round2, l)
    out_rows_gps = map( map2, ( out_rows, gps) ) + [ all_clean ]
    return out_rows_gps,r



if __name__ == '__main__':
    cl_args = parse_args()
    input_dir = '/home/owainevans/Venturecxx/examples/CP1-Quad-Rotor/data/automobile/1_straight/data/noisy'
    output_dir = '/home/owainevans/Venturecxx/examples/CP1-Quad-Rotor/data/automobile/1_straight_output'

    # extra parameters for approach 2 in addition to command_line args
    args = {'plot':False,
            'samples': 1,
            'lim_parameters':1000, # stop doing inference on params after this frame
            'freeze_on': True,
            'particle': True,   # use particle filter for inference
            'num_particles':4,
            'always_infer':True, # do inference every time step
            'window_size':2,
            'verbose':False,
            'per_block': cl_args.per_block, #mh samples per block (per timestep)
            'frames': cl_args.frames,
            
            'clean_dir': '/home/owainevans/Venturecxx/examples/CP1-Quad-Rotor/data/automobile/1_straight/data/ground',
            'dataset_name':'/home/owainevans/Venturecxx/examples/CP1-Quad-Rotor/data/automobile/1_straight_output/5_eight', 
            'input_dir': input_dir,
            'output_dir': output_dir,
            'ground': False,
            'max_time': None,
            'version': 'v2', }

    # make object equivalent to argparse given command-line args
    args = argparse.Namespace(**args)
    dataset_name = args.dataset_name
    combined_frame, clean_gps_frame = read_combined_frame()
    xlim = (-10, 10)
    ylim = (-5, 5)
    out_cols = ['SLAMGPSTime', 'SLAMLat', 'SLAMLon']
    
    approaches = dict(v1 =runRandomWalk,v2 = runApproach2)
    approach = approaches[args.version]
    

    start = time.time()
    all_mses = []
    # loop over *approach* and combine outputs
    for i in range(args.samples):
        out,r = approach()
        out_rows,gps,all_clean_gps = out
        all_clean = np.array( [ [t]+list(ar[:-1]) for t,ar in all_clean_gps] )
        mse = np.mean( (np.array(out_rows) - all_clean )**2 )
        all_mses.append( mse )
        
        st = (args.particle, args.freeze_on, args.frames, args.lim_parameters,
              args.per_block, args.window_size, mse, time.time() - start)
        print 'Summary: part %s, freeze %s, frames %i, lim_param %i, mh/block %i, k=%i, mse %.4f, elapsed %.2f'%st

    print '\nMSE for each sample:', all_mses
    
    


    out_file = '%s/slam_out_path.csv' % args.output_dir
    ensure(out_file);   writeCSV(out_file, out_cols, out_rows)
#    print "Wrote output to " + out_file
    landmarks_cols = ['SLAMBeaconX','SLAMBeaconY']; landmarks_rows = [(0, 0)]
    landmarks_file = '%s/slam_out_landmarks.csv' % args.output_dir
    writeCSV(landmarks_file, landmarks_cols, landmarks_rows)
#    print "Wrote landmarks to " + landmarks_file



