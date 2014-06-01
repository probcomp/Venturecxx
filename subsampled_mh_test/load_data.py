def loadData(data_file):
  import scipy.io
  data = scipy.io.loadmat(data_file)

  X = data['X_pca'].T
  N, D = X.shape
  Y = (data['Y']).squeeze() == True

  Xtst = data['Xtst_pca'].T
  Ntst = Xtst.shape[0]
  Ytst = (data['Ytst']).squeeze() == True
  X = X.tolist()
  Y = Y.tolist()
  Xtst = Xtst.tolist()
  Ytst = Ytst.tolist()
  return N, D, X, Y, Ntst, Xtst, Ytst
