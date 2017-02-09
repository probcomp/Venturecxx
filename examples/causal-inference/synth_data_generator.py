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


    h  = np.random.normal(0,2, (N,))
    i  = 2*h + np.random.normal(0,1, (N,))
    j =  2*h + np.random.normal(0,1, (N,))


    df = pd.DataFrame({
        "a":a, 
        "b":b, 
        "c":c, 
        "d":d, 
        "e":e, 
        "f":f, 
        "g":g, 
        "h":h, 
        "i":i, 
        "j":j})
    df.to_csv("csv_files/causal_linear.csv", index=False)

    #Plotting
    sns.pairplot(data=pd.DataFrame({"a":a, "b":b}))
    plt.title("Data of Fig. 1, subplot (i)", fontsize=20, y=1.08, x=-0.2)
    sns.pairplot(data=pd.DataFrame({"c": c, "d":d}))
    plt.title("Data of Fig. 1, subplot(ii)", fontsize=20, y=1.08, x=-0.2)
    plt.figure()
    sns.pairplot(data=pd.DataFrame({"e":e, "f": f, "g":g}))
    plt.title("Data of Fig. 1, subplot (iii)", fontsize=20, y=2.28, x=-0.8)
    sns.pairplot(data=pd.DataFrame({"h":h, "i": i, "j":j}))
    plt.title("Data of Fig. 1, subplot (iv)", fontsize=20, y=2.28, x=-0.8)

def generate_non_linear_data(N):
    sns.set_context("talk", font_scale=1.)
    np.random.seed(seed=0)

    a  = np.random.normal(0,2, (N,))
    b  = np.random.normal(0,2, (N,))

    c  = np.random.normal(0,2, (N,))
    d  = c**2 + np.random.normal(0,1, (N,))

    e  = np.random.normal(0,2, (N,))
    f  = np.random.normal(0,2, (N,))
    g =  e**2 + f**2 + np.random.normal(0,1, (N,))


    h  = np.random.normal(0,2, (N,))
    i  = h**2 + np.random.normal(0,1, (N,))
    j =  h**2 + np.random.normal(0,1, (N,))


    df = pd.DataFrame({
        "a":a, 
        "b":b, 
        "c":c, 
        "d":d, 
        "e":e, 
        "f":f, 
        "g":g, 
        "h":h, 
        "i":i, 
        "j":j})
    df.to_csv("csv_files/causal_non_linear.csv", index=False)

    #Plotting
    sns.pairplot(data=pd.DataFrame({"a":a, "b":b}))
    plt.title("Data of Fig. 1, subplot (i)", fontsize=20, y=1.08, x=-0.2)
    sns.pairplot(data=pd.DataFrame({"c": c, "d":d}))
    plt.title("Data of Fig. 1, subplot(ii)", fontsize=20, y=1.08, x=-0.2)
    plt.figure()
    sns.pairplot(data=pd.DataFrame({"e":e, "f": f, "g":g}))
    plt.title("Data of Fig. 1, subplot (iii)", fontsize=20, y=2.28, x=-0.8)
    sns.pairplot(data=pd.DataFrame({"h":h, "i": i, "j":j}))
    plt.title("Data of Fig. 1, subplot (iv)", fontsize=20, y=2.28, x=-0.8)

def flip(p):
    return np.random.uniform(0,1)

def binary_conditional_one_parent(parent):
    p = np.random.uniform(0,1,(2,))
    child = []
    for row in parent:
        if row:
            child.append([np.random.uniform(0,1) <  p[0]])
        else:
            child.append([np.random.uniform(0,1) <  p[1]])
    return np.array(child)

def binary_conditional_two_parents(parent_1, parent_2):
    p = np.random.uniform(0,1,(4,))
    child = []
    for parent_values in zip(parent_1, parent_2):
        if sum(parent_values)==0:
            child.append([np.random.uniform(0,1) <  p[0]])
        elif parent_values[0]==0 and parent_values[1]==1:
            child.append([np.random.uniform(0,1) <  p[1]])
        elif parent_values[0]==1 and parent_values[1]==0:
            child.append([np.random.uniform(0,1) <  p[2]])
        elif sum(parent_values)==2:
            child.append([np.random.uniform(0,1) <  p[3]])
        else:
            raise ValueError("incorrect parent config")
    return np.array(child)

def generate_binary_data(N):
    sns.set_context("talk", font_scale=1.)
    np.random.seed(seed=0)

    a  = np.random.randint(0,2, (N,))
    b  = np.random.randint(0,2, (N,))

    c  = np.random.randint(0,2, (N,))
    d  = binary_conditional_one_parent(c) 

    e  = np.random.randint(0,2, (N,))
    f  = np.random.randint(0,2, (N,))
    g =  binary_conditional_two_parents(e, f)


    h  = np.random.randint(0,2, (N,))
    i  = binary_conditional_one_parent(h)
    j =  binary_conditional_one_parent(h)


    df = pd.DataFrame({
        "a":a, 
        "b":b, 
        "c":c, 
        "d":d, 
        "e":e, 
        "f":f, 
        "g":g, 
        "h":h, 
        "i":i, 
        "j":j})
    df.to_csv("csv_files/causal_binary.csv", index=False)

    #Plotting
    sns.pairplot(data=pd.DataFrame({"a":a, "b":b}))
    plt.title("Data of Fig. 1, subplot (i)", fontsize=20, y=1.08, x=-0.2)
    sns.pairplot(data=pd.DataFrame({"c": c, "d":d}))
    plt.title("Data of Fig. 1, subplot(ii)", fontsize=20, y=1.08, x=-0.2)
    plt.figure()
    sns.pairplot(data=pd.DataFrame({"e":e, "f": f, "g":g}))
    plt.title("Data of Fig. 1, subplot (iii)", fontsize=20, y=2.28, x=-0.8)
    sns.pairplot(data=pd.DataFrame({"h":h, "i": i, "j":j}))
    plt.title("Data of Fig. 1, subplot (iv)", fontsize=20, y=2.28, x=-0.8)

