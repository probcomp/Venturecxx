def loadData(data_file):
  import scipy.io
  data = scipy.io.loadmat(data_file)

  if 'X_pca' in data:
    X = data['X_pca'].T
  else:
    X = data['X'].T
  N, D = X.shape
  Y = (data['Y']).squeeze() == True

  if 'Xtst_pca' in data:
    Xtst = data['Xtst_pca'].T
  else:
    Xtst = data['Xtst'].T
  Ntst = Xtst.shape[0]
  Ytst = (data['Ytst']).squeeze() == True
  X = X.tolist()
  Y = Y.tolist()
  Xtst = Xtst.tolist()
  Ytst = Ytst.tolist()
  return N, D, X, Y, Ntst, Xtst, Ytst


def loadSVData(data_file):
  import scipy.io
  data = scipy.io.loadmat(data_file)

  X = data['X'].squeeze()
  X = X.tolist()
  N = len(X)

  return N, X
