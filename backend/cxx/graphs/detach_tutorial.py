from subprocess import call
import copy

##### Tutorial 1 for regen/detach

class RenderTutorial1(object):
  def __init__(self,nodes,drg,edges,dirpath):
    self.dirpath = dirpath
    self.fmt = "pdf"
    self.i = 0
    self.nodes = nodes
    self.drg = drg
    self.edges = edges

    # isdrg
    self.stackFillColor = "grey90"
    self.detachFillColor = "white"


    # isdrg
    self.colors = { True : "gold", False : "steelblue1" }


    self.regenCounts = {node : len(self.edges[node]) for node in self.drg}

    self.regenerated = copy.deepcopy(self.nodes)
    self.stack = set()
    self.dot = ""
    self.renderDot()

  def addToStack(self,node):
    assert not node in self.stack
    assert not node in self.regenerated
    self.stack.add(node)
    self.renderDot()

  def removeFromStack(self,node):
    assert node in self.stack
    assert not node in self.regenerated
    self.stack.remove(node)
    
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
             "color" : self.colors[node in self.drg],
             "fillcolor" : self.getFillColor(node) ,
             "style" : "filled",
             "label" : self.getLabel(node),
             "penwidth" : 3,
         }

  def getFillColor(self,node):
    if node in self.stack: return self.stackFillColor
    elif node in self.regenerated: return self.colors[node in self.drg]
    else: return self.detachFillColor

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
    for (startNode,outgoingEdges) in self.edges.iteritems(): 
      for endNode in outgoingEdges:
        self.dotEdge(startNode,endNode)
    self.dot += "}"

  def edgeAttributes(self,startNode,endNode):
    return { "arrowhead" : "normal",
             "style" : "solid",
             "color" : "black" }

  def dotEdge(self,startNode,endNode):
    self.dot += str(startNode) + " -> " + str(endNode)
    self.dotAttributes(self.edgeAttributes(startNode,endNode))
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


drg = set([1,2,3,4])
nodes = set([1,2,3,4,5,6,7])
edges = {1 : [2,3,4], 2 : [5,6], 3 : [6], 4: [7] }
rt1 = RenderTutorial1(nodes,drg,edges,"tutorial_1_pdf")

operations = [ (5, [(2, [(1,[])])]),
               (6, [(2,[]),(3, [(1,[])])]),
               (7, [(4, [(1,[])])]),
             ]

# need to reverse the nested calls
def detachOperation(node,parents):
  rt1.performOperation(False,node)
  for (n,ps) in reversed(parents):
    detachOperation(n,ps)

def regenOperation(node,parents):
  if parents:
    rt1.addToStack(node)
    for (n,ps) in parents: regenOperation(n,ps)
    rt1.removeFromStack(node)

  rt1.performOperation(True,node)


for (node,parents) in reversed(operations): detachOperation(node,parents)
for (node,parents) in operations: regenOperation(node,parents)

#for node in sequence: rt1.performOperation(False,node)
#for node in reversed(sequence): rt1.performOperation(True,node)

