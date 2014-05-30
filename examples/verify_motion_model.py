import functools
import itertools
#
import numpy
#
from venture.shortcuts import make_puma_church_prime_ripl


def get_motion_params_dict(**kwargs):
    motion_params_dict = dict(
        fractional_xy_error_std = 0.0,
        fractional_heading_error_std = 0.0,
        additive_xy_error_std = 0.0,
        additive_heading_error_std = 0.0,
        )
    motion_params_dict.update(kwargs)
    return motion_params_dict

def _get_program(vehicle_a, vehicle_b, vehicle_h, vehicle_L,
        fractional_xy_error_std, fractional_heading_error_std,
        additive_xy_error_std, additive_heading_error_std,
        ):
    program_constants = """
    [assume vehicle_params (list %s %s %s %s)]
    """ % (vehicle_a, vehicle_b, vehicle_h, vehicle_L)

    program_parameters = """
    [assume fractional_xy_error_std %s]
    [assume fractional_heading_error_std %s]
    [assume additive_xy_error_std %s]
    [assume additive_heading_error_std %s]
    """ % (fractional_xy_error_std, fractional_heading_error_std,
            additive_xy_error_std, additive_heading_error_std)

    program = program_constants + program_parameters
    return program

def get_program(motion_params_dict):
    vehicle_params_dict = dict(
        vehicle_a = 0.299541,
        vehicle_b = 0.0500507,
        vehicle_h = 0,
        vehicle_L = 0.257717,
        )
    args_dict = dict()
    args_dict.update(vehicle_params_dict)
    args_dict.update(motion_params_dict)
    program = _get_program(**args_dict)
    return program

def create_venture_list(in_list):
    return '(list ' + ' '.join(map(str, in_list)) + ')'

def get_predict_motion_str(dt, pose, control):
    predict_motion_str = """
      (simulate_motion %s
                       %s
                       %s
                       vehicle_params
                       fractional_xy_error_std
                       fractional_heading_error_std
                       additive_xy_error_std
                       additive_heading_error_std
                       )
                       """ % (dt, create_venture_list(pose), create_venture_list(control))
    return predict_motion_str

def predict_forward(dt, pose, control,
        motion_params_dict, predict_N=100):
    predict_motion_str = get_predict_motion_str(dt, pose, control)
    program = get_program(motion_params_dict)
    ripl = make_puma_church_prime_ripl()
    ripl.execute_program(program)
    predicted = numpy.array([
            ripl.predict(predict_motion_str)
            for _i in range(predict_N)
            ])
    return predicted

def get_meshgrid(dt, pose, control, motion_params_dict, N_grid=40):
    def _get_linspace((center, extent)):
        return numpy.linspace(center - extent, center + extent, N_grid)
    predicted = predict_forward(dt, pose, control, motion_params_dict)
    predicted_mean = predicted.mean(axis=0)
    predicted_std = predicted.std(axis=0)
    _X, _Y, _heading = map(_get_linspace, zip(predicted_mean, predicted_std))
    _Z_arg_tuples = itertools.product(_X, _Y)
    X, Y = numpy.meshgrid(_X, _Y)
    return X, Y, _Z_arg_tuples

def get_log_density(dt, start_pose, control, motion_params_dict, N_grid):
    predict_motion_str = get_predict_motion_str(dt, start_pose, control)
    program = get_program(motion_params_dict)
    X, Y, _Z_arg_tuples = get_meshgrid(dt, start_pose, control,
            motion_params_dict, N_grid)
    ripl = make_puma_church_prime_ripl()
    def _convert(val):
        def _convert_real(val):
            return {"type":"real","value":val}
        def _convert_list(val):
            return {"type":"vector","value":map(_convert, val)}
        is_list = isinstance(val, (list, tuple))
        return _convert_list(val) if is_list else _convert_real(val)
    def get_logscore_motion(stop_pose):
        ripl.clear()
        ripl.execute_program(program)
        # FIXME: hard coding heading = 0 here
        stop_pose = list(stop_pose) + [0]
        ripl.observe(predict_motion_str, _convert(stop_pose))
        ripl.infer('(incorporate)')
        return ripl.get_global_logscore()
    #
    log_density = map(get_logscore_motion, _Z_arg_tuples)
    log_density = numpy.array(log_density).reshape((N_grid, N_grid))
    return X, Y, log_density

def plot_log_density(X, Y, Z):
    import pylab
    pylab.ion()
    pylab.show()
    from mpl_toolkits.mplot3d import Axes3D
    from matplotlib import cm
    fig = pylab.figure()
    ax = fig.gca(projection='3d')
    surf = ax.plot_surface(X, Y, Z,
            rstride=1, cstride=1, cmap=cm.coolwarm,
            linewidth=0, antialiased=False)
    fig.colorbar(surf, shrink=0.5, aspect=5)
    return

motion_params_dict = get_motion_params_dict(
    additive_xy_error_std = 0.0001,
    additive_heading_error_std = 0.0001,
    )
X, Y, log_density = get_log_density(.1, (0, 0, 0), (1, 0), motion_params_dict, 20)
plot_log_density(X, Y, log_density)
