import random
from functools import partial
#
import numpy
import pylab
pylab.ion()
pylab.show()
import matplotlib
import matplotlib.cm as cm
from matplotlib.colors import LogNorm
from scipy.stats.kde import gaussian_kde 


def get_figure(new_figure=True):
    return pylab.figure() if new_figure else pylab.gcf()

def do_hist2d(x, y, new_figure=True):
    fig = get_figure(new_figure)
    return pylab.hist2d(x, y, norm=LogNorm())

def enforce_min_value(arr, min_value=None, new_min=0):
    if min_value is not None:
        arr[arr<min_value] = new_min
        pass
    return arr

is_cmap = lambda x: isinstance(x, matplotlib.colors.LinearSegmentedColormap)
cms = filter(is_cmap, cm.__dict__.values())
count = 0
def do_kde2d(x, y, min_value=None, new_figure=True, *args, **kwargs):
    global count
    which_cm = cms[count % len(cms)]
    count += 1
    x, y = map(numpy.array, [x, y])
    xmin, xmax = x.min(), x.max()
    ymin, ymax = y.min(), y.max()
    X, Y = numpy.mgrid[xmin:xmax:100j, ymin:ymax:100j]
    positions = numpy.vstack([X.ravel(), Y.ravel()])
    values = numpy.vstack([x, y])
    kernel = gaussian_kde(values)
    Z = numpy.reshape(kernel(positions).T, X.shape)
    Z = enforce_min_value(Z, min_value)
    #
    fig = get_figure(new_figure)
    ax = fig.add_subplot(111)
    extent = [xmin, xmax, ymin, ymax]
    ax.imshow(numpy.rot90(Z), extent=extent, norm=LogNorm(),
            cmap=which_cm)
    ax.plot(x, y, 'k.', markersize=2)
    return fig

def plot_landmark((x, y), *args, **kwargs):
    kwargs.setdefault('markersize', 10)
    kwargs.setdefault('markeredgewidth', 2)
    kwargs.setdefault('markeredgecolor', 'r')
    pylab.plot(x, y, marker='x', *args, **kwargs)
    pylab.plot(x, y, marker='o', fillstyle='none', *args, **kwargs)
    pass

def ensure_3d(samples):
    shape = numpy.array(samples).shape
    is_3d = len(shape) == 3
    return samples if is_3d else [samples]

def plot_scene(samples_list, landmarks=(), min_value=None, new_figure=True,
        *args, **kwargs):
    fig = get_figure(new_figure)
    def _do_kde2d(samples):
        return do_kde2d(*zip(*samples), min_value=min_value, new_figure=False)
    samples_list = ensure_3d(samples_list)
    map(_do_kde2d, samples_list)
    map(plot_landmark, landmarks)
    return fig


if __name__ == '__main__':
    def gen_random_data(N_samples, *args, **kwargs):
        _x = numpy.random.normal(size=N_samples, *args, **kwargs)
        _y = numpy.random.normal(size=N_samples, *args, **kwargs)
        x = _x + _y
        y = _x - _y
        return x, y

    def gen_samples(N_samples, loc=(0, 0), *args, **kwargs):
        x0, y0 = loc
        x, y = gen_random_data(N_samples, *args, **kwargs)
        return zip(x + x0, y + y0)

    origin = (0, 0)
    landmark0 = (1, 2)
    landmark1 = (4, 4)
    landmark2 = (7, 9)
    landmarks = [landmark0, landmark1, landmark2]
    N_samples = 1000
    samples_list = [
            gen_samples(N_samples, loc=landmark, scale=0.5)
            for landmark in landmarks
            ]
    plot_scene(samples_list, [origin] + landmarks, min_value=.02, new_figure=True)
