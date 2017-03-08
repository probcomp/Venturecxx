import matplotlib.pyplot as plt

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
        ax.hist([chain[step] for chain in chains])
        ax.set_xlim([0,1])
        ax.set_title("M-H step %d" % (step,))
        ax.set_xlabel("weight")
        ax.set_ylabel("num samples")

plot_mcmc('mcmc.txt')
plt.show()
