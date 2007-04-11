#!/bin/bash

msg()
{
    echo 
    echo "$1"
    echo 
}



help()
{
	echo "no help yet"
}


# packages needed for the virt-factory server itself
install_server_packages()
{
    yum install -y virt-factory-server  virt-factory-wui puppet puppet-server
}


# packages needed for a node machine
# note, for this test, the machine running this script will install the server and the client code
install_client_packages()
{
    yum install -y virt-factory-nodes virt-factory-register koan puppet
}



# create the repo like the one at 
# http://virt-factory.et.redhat.com/download/repo/fc6/stable/i386/
# but with the recently built packages and synced to REMOTE_HOST so
# that the vf_server import/cobbler import can be told to sync it from there
# and create the virt-factory vf_repo repo 
setup_vf_repo_upstream()
{
    msg "setup_vf_repo_upstream"

}

setup_vf_server()
{
    msg "Setting up the config settings for vf_server"
    
    HN=`hostname`
    # FIXME: were just reposyncing the normal repo to a specific path
    # FIXME: this path shouldn't be hardcoded
    VF_REPO="http://$REMOTE_HOST/$URL_PATH/repo/fc6/devel/i386"
    cp settings settings.testing
    export HN VF_REPO
    perl -p -i -e "s/ADDRESS/\$ENV{'HN'}/g" settings.testing
    perl -p -i -e "s/VF_REPO/\$ENV{'VF_REPO'}/g" settings.testing
    cp -f settings.testing /etc/virt-factory/settings
}

setup_puppet()
{
	touch /etc/puppet/manifests/site.pp

}

start_server()
{
    /etc/init.d/puppetmaster restart
    /etc/init.d/virt-factory-server restart
    /etc/init.d/virt-factory-wui start
}


#REMOTE_USER=$USER

# note, the user you log in as needs perms to write to 
# REMOTE_PATH 
REMOTE_USER="alikins"
REMOTE_HOST="grimlock.devel.redhat.com"
REMOTE_PATH="/var/www/html/download"
URL_PATH="/download/"


# er, variables...
REBUILD=N
SYNC_REPOS=N
INSTALL_PACKAGES=Y
SETUP_PUPPET=Y
VF_SERVER_IMPORT=Y
VF_IMPORT=Y
REFRESH_DB=Y
START_SERVER=Y

# commandline parsing
while [ $# -gt 0 ]
do
    case "$1" in
        -h)  help;;
	-r) REBUILD=Y;;
	--rebuild) REBUILD=Y;;
	--sync-repos) SYNC_REPOS=Y;;
	--install-packages) INSTALL_PACKAGES=Y;;
	--skip-packages) INSTALL_PACKAGES=N;;
	--skip-puppet) SETUP_PUPPET=N;;
	--skip-import) VF_SERVER_IMPORT=N;;
	--skip-vf-import) VF_IMPORT=N;;
	--skip-db-refresh) REFRESH_DB=N;;
	--skip-server-start) START_SERVER=N;;
    esac
    shift
done

# FIXME: we should probably clone the git repo's then run the script. The script
# thats in the repo. 


if [ "$REBUILD" == "Y" ] ; then
	msg "Rebuilding everything for kicks"
	./build-it-all.sh
	
	# note, we also need to build cobbler and koan, and 
	# add them to the repo. Do we want to do this as part of
	# build-it-all.sh? probably

fi
 
# this syncs the repos to the server, and generates the yum repo.d config files
if [ "$SYNC_REPOS" == "Y" ] ; then
	msg "syncing repos"
	msg "calling sync-it-all.sh with user $REMOTE_USER"
	./sync-it-all.py --user $REMOTE_USER --hostname $REMOTE_HOST --path $REMOTE_PATH --release "devel" --distro "fc6" --urlpath $URL_PATH

fi

if [ "$REFRESH_DB" == "Y" ] ; then
    msg "Purging the db"
    rm -rf /var/lib/virt-factory/primary_db
    /usr/bin/vf_create_db.sh
fi


# FIXME: we currently dont rev packages very well, we either need to rev on every package build
# or remove all the packages first, otherwise we never pick up "new, but not newer version" packages
if [ "$INSTALL_PACKAGES" == "Y" ] ; then
    msg "configuring yum"
    cp -av repos.d/* /etc/yum.repos.d/
    
    msg "installing server packages from devel repo"
    install_server_packages

fi

if [ "$SETUP_PUPPET" == "Y" ] ; then
    msg "Setting up puppet"
    setup_puppet
fi

# do the config tweaking for the local vf_server
setup_vf_server 

# This creates the vf_repo as well, though we probably need to create the sample
# repo somewhere ($REMOTE_HOST?) and set the settings to sync from there to here,
# so that we get the fresh packages we just built
if [ "$VF_SERVER_IMPORT" == "Y" ] ; then
    msg "Starting vf_server import, this could take a while"
    
    # do the rynsc, the db import, and reposync the vf_repo's
    /usr/bin/vf_server import
fi


# NOTE: we have to do this after "vf_server import" as that creates
# the vf_repo
if [ "$INSTALL_PACKAGES" == "Y" ] ; then
    msg "Installing client packages from vf_repo"
    install_client_packages
fi


if [ "$VF_IMPORT" == "Y" ] ; then
    msg "importing profiles"
    cd profiles/
    for profile in `cat profile_manifest`
    do
      msg "importing $profile"
      /usr/bin/vf_import $profile
    done
    cd ..
fi

if [ "$START_SERVER" = "Y" ] ; then
    msg "restarting services"
    start_server
fi

