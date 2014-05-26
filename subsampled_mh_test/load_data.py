def loadData(data_file):
  import scipy.io
  data = scipy.io.loadmat(data_file)
  X = data['X_pca'].T
  N, D = X.shape
  Y = (data['Y']).squeeze() == True
  X = X.tolist()
  Y = Y.tolist()
  return N, D, X, Y
