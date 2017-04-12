import math
import sys

from venture.lite.crp import log_prob_num_tables
from venture.lite.crp import sample_num_tables
from venture.plots.p_p_plot import discrete_p_p_plot


def compare(n, alpha, iters):
    probs = [math.exp(log_prob_num_tables(k, n, alpha)) for k in range(n+1)]
    expected = zip(range(n+1), probs)
    lengths = [sample_num_tables(n, alpha) for _ in range(iters)]
    discrete_p_p_plot(expected, lengths, show=True)

if __name__ == '__main__':
    compare(int(sys.argv[1]), float(sys.argv[2]), int(sys.argv[3]))
