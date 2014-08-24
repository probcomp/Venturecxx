import json

def saveObj(obj, file_name):
  f = open(file_name, 'w')
  json.dump(obj, f)
  f.close()

def loadObj(file_name):
  f = open(file_name, 'r')
  obj = json.load(f)
  f.close()
  return obj

def loadData(data_file):
  data = loadObj(data_file)
  return data['N'], data['D'], data['X'], data['Y'], data['Ntst'], data['Xtst'], data['Ytst']

def loadSeqData(data_file):
  data = loadObj(data_file)
  return data['N'], data['X']

def loadSSMData(data_file):
  data = loadObj(data_file)
  return data['N'], data['X'], data['sig_noise']

def convertMatToJson(data_file_no_ext):
  import load_data
  N, D, X, Y, Ntst, Xtst, Ytst = load_data.loadData(data_file_no_ext+'.mat')
  data = {'N':N, 'D':D, 'X':X, 'Y':Y, 'Ntst':Ntst, 'Xtst':Xtst, 'Ytst':Ytst}
  saveObj(data, data_file_no_ext+'.json')

def convertSSMMatToJson(data_file_no_ext):
  import load_data
  N, X, sig_noise = load_data.loadSSMData(data_file_no_ext+'.mat')
  data = {'N':N, 'X':X, 'sig_noise':sig_noise}
  saveObj(data, data_file_no_ext+'.json')

