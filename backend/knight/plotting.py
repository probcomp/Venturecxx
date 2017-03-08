import numpy as np
import matplotlib.pyplot as plt

bins = np.linspace(0, 1, 50)

def plot_mcmc(filename):
    with open(filename, 'r') as f:
        chains = [[float(num) for num in line.strip().strip('[]').split(',')]
                  for line in f.readlines()]

    num_steps = len(chains[0]) - 1

    plot_schedule = [0, int(num_steps/4), int(num_steps/2),
                     int(3*num_steps/4), num_steps]
    fig = plt.figure()
    for i, step in enumerate(plot_schedule):
        ax = fig.add_subplot(len(plot_schedule), 1, i+1)
        ax.hist([chain[step] for chain in chains], bins=bins)
        ax.set_xlim([0,1])
        ax.set_title("M-H step %d" % (step,))
        ax.set_xlabel("weight")
        ax.set_ylabel("num samples")
        do_plot_rejection('rejection.txt', ax)

def plot_particles(filename):
    with open(filename, 'r') as f:
        chains = [[float(num) for num in line.strip().strip('[]').split(',')]
                  for line in f.readlines()]

    num_steps = len(chains[0])

    plot_schedule = [0, int((num_steps-1)/4), int((num_steps-1)/2),
                     int(3*(num_steps-1)/4), num_steps-1]
    fig = plt.figure()
    for i, step in enumerate(plot_schedule):
        ax = fig.add_subplot(len(plot_schedule), 1, i+1)
        ax.hist([chain[step] for chain in chains], bins=bins)
        ax.set_xlim([0,1])
        if step == 0:
            ax.set_title("With 1 particle")
        else:
            ax.set_title("With %d particles" % (step+1,))
        ax.set_xlabel("weight")
        ax.set_ylabel("num samples")
        do_plot_rejection('rejection.txt', ax)

def do_plot_rejection(filename, ax=None):
    with open(filename, 'r') as f:
        chains = [[float(num) for num in line.strip().strip('[]').split(',')]
                  for line in f.readlines()]
    if ax is None:
        plt.figure()
        ax = plt.gca()
    ax.hist([chain[0] for chain in chains], histtype='step', color='orange', bins=bins)
    return ax

def plot_rejection(filename):
    ax = do_plot_rejection(filename)
    ax.set_xlim([0,1])
    ax.set_title("Rejection sampling")
    ax.set_xlabel("weight")
    ax.set_ylabel("num samples")

# plot_mcmc('mcmc.txt')
plot_particles('particles.txt')
# plot_rejection('rejection.txt')
plt.show()
