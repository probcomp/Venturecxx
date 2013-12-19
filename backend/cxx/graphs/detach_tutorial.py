from subprocess import call
import copy

##### Tutorial 1 for regen/detach

class RenderTutorial1(object):
  def __init__(self):
    self.dirpath = "tutorial_1"
    self.fmt = "svg"
    self.i = 0
    self.drg = set([1,2,3,4])
    self.nodes = set([1,2,3,4,5,6,7])
#    self.active = None

    self.edges = [(1,2),(2,5),(2,6),(1,3),(3,6),(1,4),(4,7)]

    # (isdrg,isregened)
    self.colors = { (True,True) : "red" , 
                    (True,False) : "gold", 
                    (False,True) : "blue",
                    (False,False) : "green",
                }

    self.regenCounts = {1:3, 2:2, 3:1,4:1}

    self.regenerated = copy.deepcopy(self.nodes)
    self.dot = ""
    self.renderDot()
    
  def performOperation(self,isRegen,node):
    if isRegen and node in self.drg: self.regenNode(node)
    elif isRegen and not node in self.drg: self.attachNode(node)
    elif not isRegen and node in self.drg: self.extractNode(node)
    elif not isRegen and not node in self.drg: self.detachNode(node)

  def detachNode(self,node):
    assert node in self.regenerated
    assert not node in self.drg
    self.regenerated.remove(node)
    self.renderDot()

  def attachNode(self,node):
    assert not node in self.regenerated
    assert not node in self.drg
    self.regenerated.add(node)
    self.renderDot()

  def extractNode(self,node):
    assert node in self.regenerated
    assert node in self.drg
    self.regenCounts[node] -= 1
    if self.regenCounts[node] == 0: self.regenerated.remove(node)
    self.renderDot()

  def regenNode(self,node):
    assert node in self.drg
    if self.regenCounts[node] == 0: self.regenerated.add(node)
    self.regenCounts[node] += 1
    self.renderDot()

  def nodeAttributes(self,node):
    return { "shape" : "ellipse",
             "fillcolor" : self.colors[(node in self.drg,node in self.regenerated)],
             "style" : "filled",
             "label" : self.getLabel(node),
         }

  def getLabel(self,node):
    if node in self.drg: return self.regenCounts[node]
    else: return ""

  def dotNode(self,node):
    self.dot += str(node)
    self.dotAttributes(self.nodeAttributes(node))
    self.dot += "\n"
  
  def quote(self,s): return "\"" + str(s) + "\" "

  def dotAttribute(self,name,value):
    self.dot += self.quote(name) + "=" + self.quote(value)

  def dotAttributes(self,attributes):
    self.dot += "["
    for (name,value) in attributes.items():
      self.dotAttribute(name,value)
    self.dot += "]"
  
  def dotTrace(self):
    self.dot = "digraph {\nrankdir=BT\nfontsize=24\n"
    for node in self.nodes: self.dotNode(node)
    for edge in self.edges: self.dotEdge(edge)
    self.dot += "}"

  def edgeAttributes(self,edge):
    return { "arrowhead" : "normal",
             "style" : "solid",
             "color" : "black" }

  def dotEdge(self,edge):
    self.dot += str(edge[0]) + " -> " + str(edge[1])
    self.dotAttributes(self.edgeAttributes(edge))
    self.dot += "\n"

  def renderDot(self):
    self.dotTrace()
    self.i += 1
    name = "dot%d" % self.i
    mkdir_cmd = "mkdir -p " + self.dirpath
    print mkdir_cmd
    call(mkdir_cmd,shell=True)
    dname = self.dirpath + "/" + name + ".dot"
    oname = self.dirpath + "/" + name + "." + self.fmt
    f = open(dname,"w")
    f.write(self.dot)
    f.close()
    cmd = ["dot", "-T" + self.fmt, dname, "-o", oname]
    print cmd
    call(cmd)

rt1 = RenderTutorial1()
sequence = [7,4,1,6,3,1,2,5,2,1]

for node in sequence: rt1.performOperation(False,node)
for node in reversed(sequence): rt1.performOperation(True,node)
