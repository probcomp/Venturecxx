import matplotlib.pyplot as plt
import numpy as np
import scipy.stats as stats

n_bins = 50
bins = np.linspace(0, 1, n_bins)

def plot_sequential(filename, title_f, exact_file=None, analytic=None):
    chains = read_chains(filename)
    plot_schedule = schedule(len(chains[0]))
    fig = plt.figure(figsize=(8,12))
    if exact_file is None and analytic is None:
        fig.suptitle("%d independent replicates" % (len(chains),))
    elif analytic is not None:
        fig.suptitle("%d independent replicates, against the analytic distribution (orange outline)" \
                     % (len(chains),))
    else:
        fig.suptitle("%d independent replicates, against %d exact samples (orange outline)" \
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
        if analytic is not None:
            x = np.linspace(0, 1, 500)
            def scaled(x):
                # The area under the histogram is len(chains) *
                # (100.0/len(chains)) / n_bins
                return analytic.pdf(x) * 100.0 / n_bins
            ax.plot(x, map(scaled, x), color='orange')
            (D, pval) = stats.kstest(samples, analytic.cdf)
            title += ", K-S stat %6.4f, p-value %8.6f" % (D, pval)
        elif exact_file is not None:
            (_, rej_samples) = do_plot_exact(exact_file, ax)
            (D, pval) = stats.ks_2samp(samples, rej_samples)
            title += ", K-S stat %6.4f, p-value %8.6f" % (D, pval)
        ax.set_title(title)
    plt.tight_layout()
    plt.subplots_adjust(top=0.94)

def plot_mcmc(filename, exact_file=None, analytic=None):
    def title(step):
        return "M-H step %d" % (step,)
    plot_sequential(filename, title, exact_file=exact_file, analytic=analytic)

def plot_particles(filename, exact_file=None, analytic=None):
    def title(step):
        if step == 0:
            return "With 1 particle"
        else:
            return "With %d particles" % (step+1,)
    plot_sequential(filename, title, exact_file=exact_file, analytic=analytic)

def num_samples(filename):
    with open(filename, 'r') as f:
        return len(f.readlines())

def read_chains(filename):
    with open(filename, 'r') as f:
        return [[float(num) for num in line.strip().strip('[]').split(',')]
                for line in f.readlines()]

def chains_to_sampless(chains):
    return [[c[i] for c in chains] for i in range(len(chains[0]))]

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

def plot_ks_comparison(particle_fname, mcmc_fname, rejection_fname):
    p_sampless = chains_to_sampless(read_chains(particle_fname))
    m_sampless = chains_to_sampless(read_chains(mcmc_fname))
    r_sampless = chains_to_sampless(read_chains(rejection_fname))
    assert len(r_sampless) == 1
    plt.figure()
    ax = plt.gca()
    def compare(sampless1, sampless2, name):
        ks_test_results = [stats.ks_2samp(sampless1[i], sampless2[i])
                           for i in range(len(sampless1))]
        kss, pvals = zip(*ks_test_results)
        ax.plot(kss, label=name)
    ax.set_xlabel("Time step")
    ax.set_ylabel("K-S stat")
    compare(p_sampless, r_sampless * len(p_sampless), "SIR vs posterior")
    compare(m_sampless, r_sampless * len(m_sampless), "MCMC vs posterior")
    compare(m_sampless, p_sampless, "SIR vs MCMC")
    ax.legend()

# plot_mcmc('mcmc.txt')
# plot_particles('particles.txt')
# plot_exact('exact.txt')
# plt.show()
