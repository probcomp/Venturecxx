import json

def saveDict(x, file_base_name):
  f = open(file_base_name + '.json', 'w')
  json.dump(x, f)
  f.close()

def loadDict(file_base_name):
  f = open(file_base_name + '.json', 'r')
  x = json.load(f)
  f.close()
  return x

def loadData(file_base_name):
  data = loadDict(file_base_name + '.json')
  return data['N'], data['D'], data['X'], data['Y'], data['Ntst'], data['Xtst'], data['Ytst']

def loadSeqData(file_base_name):
  data = loadDict(file_base_name + '.json')
  return data['N'], data['X']

def loadSSMData(file_base_name):
  data = loadDict(file_base_name + '.json')
  return data['N'], data['X'], data['sig_noise']

def convertMatToJson(file_base_name):
  import io_utils
  assert not io_utils.isPyPy
  N, D, X, Y, Ntst, Xtst, Ytst = io_utils.loadData(file_base_name+'.mat')
  data = {'N':N, 'D':D, 'X':X, 'Y':Y, 'Ntst':Ntst, 'Xtst':Xtst, 'Ytst':Ytst}
  saveDict(data, file_base_name+'.json')

def convertSSMMatToJson(file_base_name):
  import io_utils
  assert not io_utils.isPyPy
  N, X, sig_noise = io_utils.loadSSMData(file_base_name+'.mat')
  data = {'N':N, 'X':X, 'sig_noise':sig_noise}
  saveDict(data, file_base_name+'.json')

