#!/bin/bash
set -e
set -v

# This script relies on an external starcluster config.  Since
# starcluster configs are currently per-developer rather than
# per-project, this script only works when axch runs it.
if [ `whoami` != "axch" ]; then
    echo "I'm sorry, I only work for axch.  Please improve me!"
    exit 1
fi

# modifiable setings
cluster_name=$1
# fall back to defaults
if [[ -z $cluster_name ]]; then
	cluster_name=venture-jenkins
fi

# Determine location of context
local_jenkins_dir=`dirname "$(readlink -f "$0")"`

# spin up the cluster
starcluster start -c venture-default -i m1.small -s 1 $cluster_name
hostname=$(starcluster listclusters $cluster_name | grep master | awk '{print $NF}')


# open up the port for jenkins
open_port_script=$local_jenkins_dir/open_master_port_via_starcluster_shell.py
starcluster shell < <(perl -pe "s/'venture-jenkins'/'$cluster_name'/" $open_port_script)


# bypass key checking
ssh -o PasswordAuthentication=no -o StrictHostKeyChecking=no jenkins@$hostname exit || true

venture_repo=git@github.com:mit-probabilistic-computing-project/Venturecxx.git
# set up jenkins: RELIES ON CODE BEING IN /root/crosscat
starcluster sshmaster $cluster_name "git clone $venture_repo venture"
starcluster sshmaster $cluster_name bash venture/jenkins/setup_jenkins.sh


# # push up jenkins configuration
# # jenkins server must be up and ready
# jenkins_uri=http://$hostname:8080
# jenkins_utils_script=$local_jenkins_dir/jenkins_utils.py
# config_filename=$local_jenkins_dir/config.xml
# python $jenkins_utils_script \
# 	--base_url $jenkins_uri \
# 	--config_filename $config_filename \
# 	-create


# notify user what hostname is
echo $hostname
