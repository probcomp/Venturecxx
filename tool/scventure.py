"""A StarCluster plugin for Venture.

Installs Venture (including development sources) on all nodes."""
from starcluster.clustersetup import ClusterSetup
from starcluster.logger import log
import os.path
import tempfile
import subprocess

class VentureInstaller(ClusterSetup): # Exceptions by default are acceptable pylint: disable=abstract-method
  def __init__(self, tarfile=None, checkout=None, unpacked_dir=None, skip_cxx=False): # pylint: disable=super-init-not-called
    # The example in docs didn't call super.
    self.tarfile = tarfile
    self.checkout = checkout
    self.skip_cxx = skip_cxx
    self.unpacked_venture_dir = unpacked_dir
    self._check_config()

  def _check_config(self):
    if self.tarfile is not None and not os.path.isfile(self.tarfile):
      log.warn("%s does not appear to be a file; ignoring." % self.tarfile)
      self.tarfile = None
    if self.checkout is not None and not os.path.isdir(self.checkout):
      log.warn("%s does not appear to be a directory; ignoring." % self.checkout)
      self.checkout = None
    if self.tarfile is None and self.checkout is None:
      # TODO What exception to raise?
      raise Exception("No source for Venture specified.  Please indicate either a tarball or a checkout.")
    if self.tarfile is not None and self.checkout is not None:
      log.warn("Checkout %s and tarfile %s given as sources for Venture.  Preferring the checkout." % (self.checkout, self.tarfile))
      self.tarfile = None
    if self.checkout is not None and self.unpacked_venture_dir is None:
      # The purpose of this complexity is to allow a user to install
      # Venture from a checkout that names the repository something
      # other than Venturecxx.
      candidate = os.path.basename(self.checkout)
      if candidate == "":
        candidate = os.path.basename(os.path.dirname(self.checkout))
      if candidate != "":
        self.unpacked_venture_dir = candidate
    if self.unpacked_venture_dir is None:
      self.unpacked_venture_dir = "Venturecxx"

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
    self.ensure_venture_source(node)
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

  def ensure_venture_source(self, node):
    if self.checkout is not None:
      tempd = tempfile.mkdtemp()
      try:
        tarfile = os.path.join(tempd, "venture.tgz")
        try:
          subprocess.call(["tar", "-czf", tarfile, self.checkout])
          node.ssh.put(tarfile, 'venture.tgz')
          node.ssh.execute('tar --extract --gunzip --file venture.tgz')
        finally:
          if os.path.isfile(tarfile):
            os.remove(tarfile)
      finally:
        os.rmdir(tempd)
    elif self.tarfile is not None:
      node.ssh.put(self.tarfile, 'venture.tgz')
      node.ssh.execute('tar --extract --gunzip --file venture.tgz')
    else:
      raise Exception("This should not happen: no Venture source found in valid config.")

  def ensure_venture(self, node):
    log.info("Building Venture on %s" % node.alias)
    node.ssh.execute('cd %s; pip install -r requirements.txt' % self.unpacked_venture_dir)
    if not self.skip_cxx:
      node.ssh.execute('cd %s; python setup.py install' % self.unpacked_venture_dir)
    else:
      node.ssh.execute('cd %s; SKIP_CXX_BACKEND=true python setup.py install' % self.unpacked_venture_dir)
