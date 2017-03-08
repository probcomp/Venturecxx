import numpy as np
import matplotlib.pyplot as plt

bins = np.linspace(0, 1, 50)

def plot_mcmc(filename, rejection_file=None):
    with open(filename, 'r') as f:
        chains = [[float(num) for num in line.strip().strip('[]').split(',')]
                  for line in f.readlines()]

    num_steps = len(chains[0]) - 1

    plot_schedule = [0, int(num_steps/4), int(num_steps/2),
                     int(3*num_steps/4), num_steps]
    fig = plt.figure(figsize=(8,12))
    if rejection_file is None:
        fig.suptitle("%d independent chains" % (len(chains),))
    else:
        fig.suptitle("%d independent chains, against %d rejection samples (orange outline)" \
                  % (len(chains), num_samples(rejection_file)))
    for i, step in enumerate(plot_schedule):
        ax = fig.add_subplot(len(plot_schedule), 1, i+1)
        ax.hist([chain[step] for chain in chains],
                bins=bins, weights=[100.0/len(chains)]*len(chains))
        ax.set_xlim([0,1])
        ax.set_ylim([0,25])
        ax.set_title("M-H step %d" % (step,))
        ax.set_xlabel("weight")
        ax.set_ylabel("% of samples")
        if rejection_file is not None:
            do_plot_rejection(rejection_file, ax)
    plt.tight_layout()
    plt.subplots_adjust(top=0.94)

def plot_particles(filename, rejection_file=None):
    with open(filename, 'r') as f:
        chains = [[float(num) for num in line.strip().strip('[]').split(',')]
                  for line in f.readlines()]

    num_steps = len(chains[0])

    plot_schedule = [0, int((num_steps-1)/4), int((num_steps-1)/2),
                     int(3*(num_steps-1)/4), num_steps-1]
    fig = plt.figure(figsize=(8,12))
    if rejection_file is None:
        fig.suptitle("%d independent replicates" % (len(chains),))
    else:
        fig.suptitle("%d independent replicates, against %d rejection samples (orange outline)" \
                  % (len(chains), num_samples(rejection_file)))
    for i, step in enumerate(plot_schedule):
        ax = fig.add_subplot(len(plot_schedule), 1, i+1)
        ax.hist([chain[step] for chain in chains],
                bins=bins, weights=[100.0/len(chains)]*len(chains))
        ax.set_xlim([0,1])
        ax.set_ylim([0,25])
        if step == 0:
            ax.set_title("With 1 particle")
        else:
            ax.set_title("With %d particles" % (step+1,))
        ax.set_xlabel("weight")
        ax.set_ylabel("% of samples")
        if rejection_file is not None:
            do_plot_rejection(rejection_file, ax)
    plt.tight_layout()
    plt.subplots_adjust(top=0.94)

def num_samples(filename):
    with open(filename, 'r') as f:
        return len(f.readlines())

def do_plot_rejection(filename, ax=None):
    with open(filename, 'r') as f:
        chains = [[float(num) for num in line.strip().strip('[]').split(',')]
                  for line in f.readlines()]
    if ax is None:
        plt.figure()
        ax = plt.gca()
    ax.hist([chain[0] for chain in chains], histtype='step', color='orange',
            bins=bins, weights=[100.0/len(chains)]*len(chains))
    return ax

def plot_rejection(filename):
    ax = do_plot_rejection(filename)
    ax.set_xlim([0,1])
    ax.set_title("Rejection sampling")
    ax.set_xlabel("weight")
    ax.set_ylabel("num samples")

# plot_mcmc('mcmc.txt')
# plot_particles('particles.txt')
# plot_rejection('rejection.txt')
# plt.show()
