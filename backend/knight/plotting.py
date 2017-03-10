import matplotlib.pyplot as plt
import numpy as np
import scipy.stats as stats

bins = np.linspace(0, 1, 50)

def plot_mcmc(filename, exact_file=None):
    with open(filename, 'r') as f:
        chains = [[float(num) for num in line.strip().strip('[]').split(',')]
                  for line in f.readlines()]

    num_steps = len(chains[0]) - 1

    plot_schedule = [0, int(num_steps/4), int(num_steps/2),
                     int(3*num_steps/4), num_steps]
    fig = plt.figure(figsize=(8,12))
    if exact_file is None:
        fig.suptitle("%d independent chains" % (len(chains),))
    else:
        fig.suptitle("%d independent chains, against %d exact samples (orange outline)" \
                     % (len(chains), num_samples(exact_file)))
    for i, step in enumerate(plot_schedule):
        ax = fig.add_subplot(len(plot_schedule), 1, i+1)
        samples = [chain[step] for chain in chains]
        ax.hist(samples, bins=bins, weights=[100.0/len(chains)]*len(chains))
        ax.set_xlim([0,1])
        ax.set_ylim([0,25])
        title = "M-H step %d" % (step,)
        ax.set_xlabel("weight")
        ax.set_ylabel("% of samples")
        if exact_file is not None:
            (_, rej_samples) = do_plot_exact(exact_file, ax)
            (D, pval) = stats.ks_2samp(samples, rej_samples)
            title += ", K-S stat %6.4f, p-value %8.6f" % (D, pval)
        ax.set_title(title)
    plt.tight_layout()
    plt.subplots_adjust(top=0.94)

def plot_particles(filename, exact_file=None):
    with open(filename, 'r') as f:
        chains = [[float(num) for num in line.strip().strip('[]').split(',')]
                  for line in f.readlines()]

    num_steps = len(chains[0])

    plot_schedule = [0, int((num_steps-1)/4), int((num_steps-1)/2),
                     int(3*(num_steps-1)/4), num_steps-1]
    fig = plt.figure(figsize=(8,12))
    if exact_file is None:
        fig.suptitle("%d independent replicates" % (len(chains),))
    else:
        fig.suptitle("%d independent replicates, against %d exact samples (orange outline)" \
                     % (len(chains), num_samples(exact_file)))
    for i, step in enumerate(plot_schedule):
        ax = fig.add_subplot(len(plot_schedule), 1, i+1)
        samples = [chain[step] for chain in chains]
        ax.hist(samples, bins=bins, weights=[100.0/len(chains)]*len(chains))
        ax.set_xlim([0,1])
        ax.set_ylim([0,25])
        if step == 0:
            title = "With 1 particle"
        else:
            title = "With %d particles" % (step+1,)
        ax.set_xlabel("weight")
        ax.set_ylabel("% of samples")
        if exact_file is not None:
            (_, rej_samples) = do_plot_exact(exact_file, ax)
            (D, pval) = stats.ks_2samp(samples, rej_samples)
            title += ", K-S stat %6.4f, p-value %8.6f" % (D, pval)
        ax.set_title(title)
    plt.tight_layout()
    plt.subplots_adjust(top=0.94)

def num_samples(filename):
    with open(filename, 'r') as f:
        return len(f.readlines())

def do_plot_exact(filename, ax=None):
    with open(filename, 'r') as f:
        chains = [[float(num) for num in line.strip().strip('[]').split(',')]
                  for line in f.readlines()]
    if ax is None:
        plt.figure()
        ax = plt.gca()
    samples = [chain[0] for chain in chains]
    ax.hist(samples, histtype='step', color='orange',
            bins=bins, weights=[100.0/len(chains)]*len(chains))
    return (ax, samples)

def plot_exact(filename):
    (ax, _) = do_plot_exact(filename)
    ax.set_xlim([0,1])
    ax.set_title("Exact sampling")
    ax.set_xlabel("weight")
    ax.set_ylabel("num samples")

# plot_mcmc('mcmc.txt')
# plot_particles('particles.txt')
# plot_exact('exact.txt')
# plt.show()
