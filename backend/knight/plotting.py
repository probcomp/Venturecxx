import matplotlib.pyplot as plt
import numpy as np
import scipy.stats as stats
from scipy.stats import distributions

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
    title = "K-S distances of SIR and single-site resimulation M-H\n" \
        + "from the posterior and from each other,\n" \
        + "on the trick coin problem,\n" \
        + "as a function of inference effort."
    if len(p_sampless[0]) == len(m_sampless[0]) and \
        len(p_sampless[0]) == len(r_sampless[0]):
        # Each distribution is represented with the same number of samples
        num_samples = len(p_sampless[0])
        title += " %d samples." % (num_samples,)
        ks_cutoff = ks_stat_cutoff(num_samples, num_samples, 0.05)
        ax.plot((0, max(len(p_sampless), len(m_sampless))-1), (ks_cutoff, ks_cutoff), '-', label="Distributions are different at 0.05 level")
    ax.set_title(title)
    ax.legend()
    plt.tight_layout()

def two_sample_p_value(n1, n2, d):
    # Compute the p-value for a given value of the K-S statistic.
    # Copied from scipy.stats, inside ks_2samp.
    en = np.sqrt(n1 * n2 / float(n1 + n2))
    try:
        prob = distributions.kstwobign.sf((en + 0.12 + 0.11 / en) * d)
    except:
        prob = 1.0
    return prob

def monotone_inverse(f, v, low, high):
    assert high > low, "%20.18f should be more than %20.18f" % (high, low)
    if abs(low - high) < 1e-12:
        return low
    mid = (low + high) / 2
    fm = f(mid)
    if fm < v:
        return monotone_inverse(f, v, mid, high)
    else:
        return monotone_inverse(f, v, low, mid)

def ks_stat_cutoff(n1, n2, p):
    """Return the maximum value of the K-S stat such that a two-sample
    test with samples sized n1 and n2 has p-value in excess of p.
    """
    def f(d):
        return -two_sample_p_value(n1, n2, d) # Negate so it is increasing
    return monotone_inverse(f, -p, 0.0, 1.0)

# plot_mcmc('mcmc.txt')
# plot_particles('particles.txt')
# plot_exact('exact.txt')
# plt.show()
