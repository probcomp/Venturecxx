import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
def generate_linear_data(N):
    sns.set_context("talk", font_scale=1.)
    np.random.seed(seed=0)
    a  = np.random.normal(0,2, (N,))
    b  = np.random.normal(0,2, (N,))
    c  = np.random.normal(0,2, (N,))
    d  = 3*c + np.random.normal(0,1, (N,))
    e  = np.random.normal(0,2, (N,))
    f  = np.random.normal(0,2, (N,))
    g =  2*e + 2*f + np.random.normal(0,1, (N,))
    df = pd.DataFrame({"a":a, "b":b, "c": c, "d":d, "e":e, "f": f, "g":g})
    df.to_csv("csv_files/causal_linear.csv", index=False)
    sns.pairplot(data=pd.DataFrame({"a":a, "b":b}))
    plt.title("Data of Fig. 1, subplot (i)", fontsize=20, y=1.08, x=-0.2)
    sns.pairplot(data=pd.DataFrame({"c": c, "d":d}))
    plt.title("Data of Fig. 1, subplot(ii)", fontsize=20, y=1.08, x=-0.1)
    plt.figure()
    sns.pairplot(data=pd.DataFrame({"e":e, "f": f, "g":g}))
    plt.title("Data of Fig. 1, subplot (iii)", fontsize=20, y=2.28, x=-0.8)
