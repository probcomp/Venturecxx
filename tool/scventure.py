"""A StarCluster plugin for Venture.

Installs Venture (including development sources) on all nodes."""
from starcluster.clustersetup import ClusterSetup
from starcluster.logger import log

class VentureInstaller(ClusterSetup):
  def __init__(self, tarfile, skip_cxx=False):
    self.tarfile = tarfile
    self.skip_cxx = skip_cxx

  def run(self, nodes, master, user, user_shell, volumes):
    for node in nodes:
      log.info("Installing Venture on %s" % node.alias)
      self.install_venture(node)

  def install_venture(self, node):
    self.ensure_basics(node)
    if not self.skip_cxx:
      self.prepare_for_c11(node)
      self.ensure_c11(node)
    self.ensure_python_deps(node)
    self.ensure_venture(node)

  def ensure_basics(self, node):
    log.info("Ensuring basic dependencies present on %s" % node.alias)
    node.apt_command('update')
    node.apt_install('git python-pip python-virtualenv')
    node.ssh.execute('pip install -U distribute')

  def prepare_for_c11(self, node):
    log.info("Preparing %s for C++11" % node.alias)
    node.apt_install('libboost1.48-all-dev libgsl0-dev cmake make ccache')

  def ensure_c11(self, node):
    log.info("Installing C++11 on %s" % node.alias)
    node.apt_install('python-software-properties')
    node.ssh.execute('add-apt-repository -y ppa:ubuntu-toolchain-r/test')
    node.apt_command('update')
    node.apt_install('gcc-4.8 g++-4.8')
    node.ssh.execute('update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-4.8 50')
    node.ssh.execute('update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-4.8 50')

  def ensure_python_deps(self, node):
    log.info("Installing Python dependencies on %s" % node.alias)
    node.apt_install('python-pyparsing python-flask python-requests python-numpy python-matplotlib')

  def ensure_venture(self, node):
    log.info("Installing Venture on %s" % node.alias)
    node.ssh.put(self.tarfile, 'venture.tgz')
    node.ssh.execute('tar --extract --gunzip --file venture.tgz')
    node.ssh.execute('cd Venturecxx; pip install -r requirements.txt')
    if not self.skip_cxx:
      node.ssh.execute('cd Venturecxx; python setup.py install')
    else:
      node.ssh.execute('cd Venturecxx; SKIP_CXX_BACKEND=true python setup.py install')
