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

# TODO Add code for detecting whether Jenkins is controllable by ssh,
# and instructing the human user to make it so if not.

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

def is_jenkins_accessible_by_ssh():
    return len(queryit(jenkins_ssh_command("who-am-i") + " | grep authenticated")) > 0

def ensure_jenkins_accessible_by_ssh():
    if is_jenkins_accessible_by_ssh():
        print "Found Jenkins to be accessible by ssh"
    else:
        print """
Jenkins security appears not to be set up, and this script is too dumb
to do it automatically.

1) Please set up Jenkins security:
   - Browse http://probcomp-3.csail.mit.edu:8080
   - Navigate "Manage Jenkins" -> "Configure Global Security"
     - Check "Enable security"
     - Select "Jenkins' own user database"
     - Uncheck "Allow users to sign up"
     - Select "Logged-in users can do anything"
     - Your option on "Prevent Cross Site Request Forgery exploits"
    - Click "Save"

2) Please create a user account for youself with Jenkins:
   - I think any sort of clicking around should give an account
     creation screen

3) Please upload your ssh public key to your Jenkins user account:
   - Browse http://probcomp-3.csail.mit.edu:8080
   - Navigate "People" -> your user name -> "Configure"
     - Paste in the public key, taking care of any copying artifacts
   - Click "Save"

4) While you're at it, please configure the proper number of
   executors:
   - Browse http://probcomp-3.csail.mit.edu:8080
   - Navigate "Manage Jenkins" -> "Configure System"
     - Fill in the form
   - Click "Save"

5) Run this script again when done
"""
        exit(1)

def jenkins_installed_plugins():
    return queryit(jenkins_ssh_command("list-plugins | cut -f 1 -d ' '")).split()

need_jenkins_restart = False

def ensure_plugins():
    global need_jenkins_restart
    plugins = jenkins_installed_plugins()
    for p in ["git", "github", "jenkins-flowdock-plugin", "greenballs"]:
        if p not in plugins:
            print "Installing Jenkins plugin " + p
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
        print "Restarting Jenkins"
        restart_jenkins()
    else:
        print "No need to restart Jenkins"

def ensure_jenkins_trusts_github():
    print "Ensuring that Jenkins trusts github"
    doit("sudo -u jenkins ssh -o PasswordAuthentication=no -o StrictHostKeyChecking=no github.com exit || true")

jenkins_home = "/var/lib/jenkins/"

def ensure_headless_matplotlib():
    print "Ensuring that Jenkins's matplotlib works headless"
    doit("sudo mkdir -p " + jenkins_home + ".matplotlib")
    doit("echo 'backend: Agg' | sudo tee " + jenkins_home + ".matplotlib/matplotlibrc")
    doit("sudo chown -R jenkins " + jenkins_home + ".matplotlib")

def github_trusts_jenkins():
    return len(queryit("git ls-remote git@github.com:mit-probabilistic-computing-project/Venturecxx.git | grep HEAD")) > 0

def ensure_github_trusts_jenkins():
    if github_trusts_jenkins():
        print "Found that Github trusts Jenkins"
    else:
        print """
Jenkins does not appear to have credentials to pull from Github,
and this script is too dumb to provide them automatically.

Please set up ssh access for Jenkins to Github:

1) Create a public-private key pair for the jenkins user if needed,
   e.g. with
     sudo -u jenkins ssh-keygen

2) Log in to the mit-pcp-jenkins account on github.com and upload
   the public key

3) Teach Jenkins to use the public key
   - Browse http://probcomp-3.csail.mit.edu:8080
   - Navigate "Credentials" -> "Global credentials" -> "Add Credentials"
     - Select "SSH Username with private key" in the "Kind dropdown"
     - The username is mit-pcp-jenkins
     - The private key is whereever you created it
       - If you supplied an encryption phrase for the key, it's under
         the "Advanced" button
   - Click "OK"

4) Make the jobs use that credential to access the repository
   - Either configure all of them individually, OR
   - Configure one, then use the functions discover_credential_id and
     replace_credential_id_locally from this file to edit the config
     files of the others, then rerun this script to upload the new job
     definitions.
"""

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
    ensure_jenkins_accessible_by_ssh()
    ensure_plugins()
    restart_jenkins_if_needed()
    ensure_jenkins_trusts_github()
    ensure_headless_matplotlib()
    give_jenkins_virtualenv_if_needed()
    ensure_jobs()
    ensure_github_trusts_jenkins()

def discover_credential_id(job):
    return queryit(jenkins_ssh_command("get-job " + job) + " | grep credentialsId")

def replace_credential_id_locally(new_id_string):
    for name in queryit("ls *.config.xml | cut -f 1 -d '.'").split():
        doit("sed --in-place='' --expression='s/<credentialsId>.*<\\/credentialsId>/" + new_id_string + "/' " + name + ".config.xml")

def give_jenkins_virtualenv():
    doit("cd /var/lib/jenkins; sudo -u jenkins virtualenv env")

def jenkins_has_virtualenv():
    return len(queryit("ls /var/lib/jenkins/ | grep env")) > 0

def give_jenkins_virtualenv_if_needed():
    if not jenkins_has_virtualenv():
        print "Setting up virtualenv for Jenkins"
        give_jenkins_virtualenv()
    else:
        print "Found Jenkins virtualenv named 'env'"

if __name__ == '__main__':
    # print discover_credential_id("venture-crashes")
    # replace_credential_id_locally("<credentialsId>2fd68a05-da40-45e1-a59c-32e795448dd5<\\/credentialsId>")
    # ensure_jobs()
    main()
