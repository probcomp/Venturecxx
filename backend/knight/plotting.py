import matplotlib.pyplot as plt

with open('mcmc.txt', 'r') as f:
    chains = [[float(num) for num in line.strip().strip('[]').split(',')]
              for line in f.readlines()]

num_steps = len(chains[0]) - 1

fig = plt.figure()
for i in range(num_steps+1):
    ax = fig.add_subplot(num_steps+1, 1, i)
    ax.hist([chain[i] for chain in chains])
    ax.set_xlim([0,1])

plt.show()
