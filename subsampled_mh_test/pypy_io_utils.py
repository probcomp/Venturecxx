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

