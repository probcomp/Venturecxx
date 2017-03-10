import matplotlib.pyplot as plt
import numpy as np
import scipy.stats as stats

bins = np.linspace(0, 1, 50)

def plot_sequential(filename, title_f, exact_file=None):
    chains = read_chains(filename)
    plot_schedule = schedule(len(chains[0]))
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
        title = title_f(step)
        ax.set_xlabel("weight")
        ax.set_ylabel("% of samples")
        if exact_file is not None:
            (_, rej_samples) = do_plot_exact(exact_file, ax)
            (D, pval) = stats.ks_2samp(samples, rej_samples)
            title += ", K-S stat %6.4f, p-value %8.6f" % (D, pval)
        ax.set_title(title)
    plt.tight_layout()
    plt.subplots_adjust(top=0.94)

def plot_mcmc(filename, exact_file=None):
    def title(step):
        return "M-H step %d" % (step,)
    plot_sequential(filename, title, exact_file=exact_file)

def plot_particles(filename, exact_file=None):
    def title(step):
        if step == 0:
            return "With 1 particle"
        else:
            return "With %d particles" % (step+1,)
    plot_sequential(filename, title, exact_file=exact_file)

def num_samples(filename):
    with open(filename, 'r') as f:
        return len(f.readlines())

def read_chains(filename):
    with open(filename, 'r') as f:
        return [[float(num) for num in line.strip().strip('[]').split(',')]
                for line in f.readlines()]

def schedule(chain_len):
    max_stage = chain_len - 1
    return [0, int(max_stage/4), int(max_stage/2),
            int(3*max_stage/4), max_stage]

def do_plot_exact(filename, ax=None):
    chains = read_chains(filename)
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
