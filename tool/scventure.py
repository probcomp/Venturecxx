"""A StarCluster plugin for Venture.

Installs Venture (including development sources) on all nodes."""
from starcluster.clustersetup import ClusterSetup
from starcluster.logger import log

class VentureInstaller(ClusterSetup):
  def __init__(self):
    pass

  def run(self, nodes, master, user, user_shell, volumes):
    for node in nodes:
      log.info("Installing Venture on %s" % node.alias)
      self.install_venture(node)

  def install_venture(self, node):
    self.prepare_for_c11(node)
    self.ensure_c11(node)
    self.ensure_python_deps(node)
    self.ensure_venture(node)

  def prepare_for_c11(self, node):
    node.ssh.execute('apt-get update')
    node.ssh.execute('apt-get install -y libboost1.48-all-dev libgsl0-dev cmake make git python-pip python-virtualenv ccache')
    node.ssh.execute('pip install -U distribute')

  def ensure_c11(self, node):
    node.ssh.execute('apt-get install -y python-software-properties')
    node.ssh.execute('add-apt-repository -y ppa:ubuntu-toolchain-r/test')
    node.ssh.execute('apt-get update')
    node.ssh.execute('apt-get install -y gcc-4.8 g++-4.8')
    node.ssh.execute('update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-4.8 50')
    node.ssh.execute('update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-4.8 50')

  def ensure_python_deps(self, node):
    node.ssh.execute('apt-get install -y python-pyparsing python-flask python-requests python-numpy python-matplotlib')

  def ensure_venture(self, node):
    # TODO get the source from somewhere
    node.ssh.execute('pip install -r requirements.txt')
    node.ssh.execute('python setup.py install')
