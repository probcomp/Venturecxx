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
    sns.pairplot(data=pd.DataFrame({"a":a, "b":b, "c": c, "d":d}))
    plt.title("Columns of subplots (a) and (b)", fontsize=20, y=3.48, x=-1.5)
    plt.figure()
    sns.pairplot(data=pd.DataFrame({"e":e, "f": f, "g":g}))
    plt.title("Columns of subplot (c)", fontsize=20, y=2.28, x=-0.5)
