#!/usr/bin/python

import sys
import os
import time
import subprocess

def tryit(command):
    print command
    return os.system(command)

def doit(command):
    status = tryit(command)
    if status != 0:
        raise "Command failed!"    

def queryit(command):
    return subprocess.check_output(command, shell=True).strip()

def is_exe(fpath):
    return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

def is_read(fpath):
    return os.path.isfile(fpath) and os.access(fpath, os.R_OK)

def is_jenkins_installed():
    return is_exe("/etc/init.d/jenkins")

def install_jenkins():
    doit("wget -q -O - https://jenkins-ci.org/debian/jenkins-ci.org.key | sudo apt-key add -")
    doit("sudo sh -c 'echo deb http://pkg.jenkins-ci.org/debian binary/ > /etc/apt/sources.list.d/jenkins.list'")
    doit("sudo apt-get update")
    doit("sudo apt-get install jenkins")

def install_jenkins_if_needed():
    if not is_jenkins_installed():
        print "Installing Jenkins"
        install_jenkins()
    else:
        print "Found Jenkins installation"

def wait_for_web_response(url):
    # TODO There has got to be a pure-Python way to do this
    cmd = "wget " + url + "2>/dev/null 1>/dev/null"
    status = tryit(cmd)
    while status != 0:
        time.sleep(2)
        status = tryit(cmd)

# It seems the Java client has no facilities for setting up security
# settings or authentication :(

# Configure Global Security
# - Jenkins' own user database
#   - Do not allow users to sign up
# - Logged-in users can do anything
# - Prevent cross-site request forgery
# Yes, you can create the first user account afterward

# People -> yourself -> configure -> upload ssh public key
# - Pay attention to possible copy-paste problems caused by line-wrapping

def discover_jenkins_ssh_port():
    return queryit('curl -s -I http://probcomp-3.csail.mit.edu:8080 | grep "X-SSH-Endpoint" | cut -f 3 -d ":"')

cached_port = None

def jenkins_ssh_port():
    global cached_port
    if cached_port is None:
        cached_port = discover_jenkins_ssh_port()
    return cached_port

def jenkins_ssh_command(command):
    return "ssh -p " + jenkins_ssh_port() + " localhost " + command

def jenkins_ssh_query(command):
    return queryit("ssh -p " + jenkins_ssh_port() + " localhost " + command).strip()

def jenkins_installed_plugins():
    return queryit(jenkins_ssh_command("list-plugins | cut -f 1 -d ' '")).split()

need_jenkins_restart = False

def ensure_plugins():
    global need_jenkins_restart
    plugins = jenkins_installed_plugins()
    for p in ["git", "github", "jenkins-flowdock-plugin", "greenballs"]:
        if p not in plugins:
            doit(jenkins_ssh_command("install-plugin " + p))
            need_jenkins_restart = True
        else:
            print "Found Jenkins plugin " + p

def restart_jenkins():
    global cached_port
    global need_jenkins_restart
    doit(jenkins_ssh_command("safe-restart"))
    wait_for_web_response("http://probcomp-3.csail.mit.edu:8080")
    cached_port = None
    need_jenkins_restart = False

def restart_jenkins_if_needed():
    global need_jenkins_restart
    if need_jenkins_restart:
        restart_jenkins()
    else:
        print "No need to restart Jenkins"

jenkins_home = "/var/lib/jenkins/"

def ensure_headless_matplotlib():
    doit("sudo mkdir -p " + jenkins_home + ".matplotlib")
    doit("echo 'backend: Agg' | sudo tee " + jenkins_home + ".matplotlib/matplotlibrc")
    doit("sudo chown -R jenkins " + jenkins_home + ".matplotlib")

def ensure_jenkins_trusts_github():
    doit("sudo -u jenkins ssh -o PasswordAuthentication=no -o StrictHostKeyChecking=no github.com exit || true")

def jenkins_create_job(name):
    doit("cat " + name + ".config.xml | " + jenkins_ssh_command("create-job " + name))

def jenkins_update_job(name):
    doit("cat " + name + ".config.xml | " + jenkins_ssh_command("update-job " + name))

def jenkins_get_job(name):
    doit(jenkins_ssh_command("get-job " + name) + " > " + name + ".config.xml")

def ensure_jobs():
    local_jobs = queryit("ls *.config.xml | cut -f 1 -d '.'").split()
    remote_jobs = queryit(jenkins_ssh_command("list-jobs")).split()
    for job in local_jobs:
        if job in remote_jobs:
            print "Found job " + job + ", updating"
            jenkins_update_job(job)
        else:
            print "Creating job " + job
            jenkins_create_job(job)

def save_jobs():
    remote_jobs = queryit(jenkins_ssh_command("list-jobs")).split()
    for job in remote_jobs:
        jenkins_get_job(job)

def main():
    install_jenkins_if_needed()
    ensure_plugins()
    restart_jenkins_if_needed()
    ensure_jenkins_trusts_github()
    ensure_headless_matplotlib()
    ensure_jobs()

if __name__ == '__main__':
    ensure_jenkins_trusts_github()
