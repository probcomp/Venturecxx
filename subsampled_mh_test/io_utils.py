import platform
isPyPy = platform.python_implementation() == "PyPy"
if not isPyPy:
  import scipy.io

  def loadData(file_base_name):
    data = scipy.io.loadmat(file_base_name)

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

  def loadSeqData(file_base_name):
    data = scipy.io.loadmat(file_base_name)

    X = data['X'].squeeze()
    X = X.tolist()
    N = len(X)

    return N, X

  def loadSSMData(file_base_name):
    data = scipy.io.loadmat(file_base_name)

    X = data['X'].squeeze()
    X = X.tolist()
    N = len(X)

    sig_noise = float(data['sig_noise'])

    return N, X, sig_noise

  def saveDict(x, file_base_name):
    scipy.io.savemat(file_base_name, x)

else:
  from pypy_io_utils import loadData, loadSeqData, loadSSMData, saveDict

