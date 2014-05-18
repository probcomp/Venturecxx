import os
import math
#
import numpy
import pandas
import pylab
pylab.ion()
pylab.show()



def get_initial_state(gps_frame):
    # first_row = gps_frame.irow(0)
    first_row = gps_frame.irow(1)
    return (first_row.heading, first_row.x, first_row.y)

def get_ackerman_parameters():
    parameter_dict = dict(
        L=0.257717,
        h=0,
        b=0.0500507,
        a=0.299541,
        )
    return parameter_dict

def get_initialization(initial_state, velocity, steering):
    initialization = dict(
        initial_state=initial_state,
        initial_velocity=velocity,
        initial_steering_angle=steering,
        )
    return initialization

def get_ackerman_config(initial_state, velocity, steering):
    ackerman_config = dict()
    ackerman_config.update(get_ackerman_parameters())
    ackerman_config.update(get_initialization(initial_state, velocity,
        steering))
    return ackerman_config

def read_frame(filename, dirname='', index_col=None, colname_map=None):
    full_filename = os.path.join(dirname, filename)
    frame = pandas.read_csv(full_filename, index_col=index_col)
    if colname_map is not None:
        frame = frame.rename(columns=colname_map)
        pass
    return frame

def DeadReckoning(initial_state, dataset):
    control_velocities = dataset['Velocity'].values
    control_steerings = dataset['Steering'].values
    dts = numpy.diff(dataset.index.values)
    first_control_velocity, control_velocities = control_velocities[0], control_velocities[1:]
    first_control_steering, control_steerings = control_steerings[0], control_steerings[1:]
    ackerman_config = get_ackerman_config(initial_state, first_control_velocity,
            first_control_steering)
    vehicleModel = AckermanVehicle(**ackerman_config)

    elapsed_time = 0
    elapsed_times = [elapsed_time]
    states = [ackerman_config['initial_state']]
    for dt, control_velocity, control_steering in zip(dts, control_velocities, control_steerings):
        elapsed_time += dt
        elapsed_times.append(elapsed_time)
        vehicleModel.predict(dt)
        states.append(vehicleModel.state)
        vehicleModel.new_steering(control_velocity, control_steering)
    columns = ['heading', 'x', 'y']
    states_frame = pandas.DataFrame(states, index=elapsed_times, columns=columns)
    return states_frame

def NormalizeAngle(angle):
    return angle
    if angle > math.pi:
        return angle-math.pi*2
    if angle < -math.pi:
        return angle+math.pi*2
    return angle

class AckermanVehicle:
    ## Constructor.  Requires specifying intrinsic knowledge of vehicle.
    # @param L Distance between front and rear axles.
    # @param h Distance between center of rear axle and encoder.
    # @param b Vertical distance from rear axle to laser.
    # @param a Horizontal distance from rear axle to laser.
    # @param init_state Initial position and heading.
    # @param init_Ve Initial forward (or backward) velocity.
    # @param init_steer_a Initial steering angle.
    def __init__(self, L, h, b, a, initial_state, initial_velocity,
            initial_steering_angle):
        self.L = L
        self.h = h
        self.b = b
        self.a = a
        self.state = initial_state
        self.forward_velocity = initial_velocity
        self.steering_angle = initial_steering_angle
        self.center_velocity = self.measuredToVehicleCenter()
        pass

    ## Updates the state vector with a prediction of motion for the past timestep.
    # @param dt The amount of time (in seconds) that have elapsed.
    def predict(self, dt):
        L = self.L
        steering_angle = self.steering_angle
        heading, x, y = self.state
        center_velocity = self.center_velocity
        forward_velocity = self.forward_velocity
        a = self.a
        b = self.b
        # Angular velocity times dt -- angular dist
        angular_displacement = dt * center_velocity / L * math.tan(steering_angle) 
        dx, dy = get_dx_dy(dt, center_velocity, heading, angular_displacement, a, b)
        new_theta = NormalizeAngle(heading + angular_displacement)
        state = (new_theta, x + dx, y + dy)
        #
        self.state = state

    def measuredToVehicleCenter(self):
        ratio = self.h / self.L
        divisor = 1 - ratio * math.tan(self.steering_angle)
        return self.forward_velocity / divisor

    def new_steering(self, forward_velocity, steering_angle):
        self.forward_velocity = forward_velocity
        self.steering_angle = steering_angle
        self.center_velocity = self.measuredToVehicleCenter()

def get_dx_dy(dt, center_velocity, heading, angular_displacement, a, b):
    sin_heading, cos_heading = math.sin(heading), math.cos(heading)
    dx_base = dt * center_velocity * cos_heading
    dx_adjustment = -1 * angular_displacement * (a * sin_heading + b * cos_heading)
    dx = dx_base + dx_adjustment
    dy_base = dt * center_velocity * sin_heading
    dy_adjustment = angular_displacement * (a * cos_heading - b * sin_heading)
    dy = dy_base + dy_adjustment
    return dx, dy

def plot_frame(frame):
    import pylab
    pylab.ion()
    pylab.show()
    fig = pylab.figure()
    pylab.subplot(211)
    frame.x.plot()
    frame.y.plot()
    pylab.subplot(212)
    (frame.heading * 180. / math.pi).plot()
    #
    pylab.figure()
    pylab.plot(frame.x, frame. y)
    return fig

def get_velocity(frame, end_row_idx, start_row_idx=None):
    start_row_idx = start_row_idx if start_row_idx else end_row_idx - 1
    end_row, start_row = frame.irow(end_row_idx), frame.irow(start_row_idx)
    delta_series = end_row - start_row
    dt = end_row.name - start_row.name
    ds = math.sqrt(delta_series.x**2 + delta_series.y**2)
    return ds / dt


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset_name', type=str, default='5_eight')
    args = parser.parse_args()
    #
    dataset_name = args.dataset_name
    base_dir = '/home/dlovell/Desktop/PPAML/CP1-Quad-Rotor/data/automobile/'
    dirname = os.path.join(base_dir, dataset_name, 'data')
    landmark_filename = 'obstacles.csv'
    control_filename = 'ground/slam_control.csv'
    gps_filename = 'ground/slam_gps.csv'
    sensor_filename = 'slam_sensor.csv'
    control_index_col = 'Time_VS'
    gps_index_col = 'TimeGPS'
    gps_to_target = dict(GPSLat='y', GPSLon='x', Orientation='heading')
    #
    gps_frame = read_frame(gps_filename, dirname=dirname,
            index_col=gps_index_col, colname_map=gps_to_target)
    control_frame = read_frame(control_filename, dirname=dirname,
            index_col=control_index_col)
    initial_state = get_initial_state(gps_frame)
    states_frame = DeadReckoning(initial_state, control_frame)
    #
    all_times = read_frame(sensor_filename, dirname=dirname, index_col=None).Time
    all_times = states_frame.index.union(pandas.Index(all_times))
    states_frame = states_frame.reindex(all_times).interpolate()
    gps_frame.reindex(columns=states_frame.columns)
    #
    plot_frame(gps_frame)
    pylab.title('gps_frame')
    plot_frame(states_frame)
    pylab.title('states_frame')

    # why don't these align?  Do one by hand
    # perhaps where same control is true within two gps readings
