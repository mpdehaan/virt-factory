#!/bin/bash


#REMOTE_USER=$USER

# note, the user you log in as needs perms to write to 
# REMOTE_PATH 
REMOTE_USER="alikins"
REMOTE_HOST="grimlock.devel.redhat.com"
REMOTE_PATH="/var/www/html/download"
URL_PATH="/download/"
DEFAULT_PROFILE="test1"

BUILD_PATH="/tmp/vf-test"
VF_SERVER_URL="http://172.16.59.218:5150"


# er, variables...
REBUILD=N
FRESH_CHCKOUT=N
SYNC_REPOS=N
INSTALL_PACKAGES=Y
SETUP_PUPPET=Y
VF_SERVER_IMPORT=Y
VF_IMPORT=Y
REFRESH_DB=Y
START_SERVICES=Y
REGISTER_SYSTEM=Y
REMOVE_PACKAGES=Y
CLEANUP_COBBLER=Y
CLEANUP_YUM=Y

msg()
{
    echo 
    echo "============ $1 ============"
    echo 
}

help()
{
	echo "no help yet"
}


check_out_code()
{
    rm -rf $BUILD_PATH
    mkdir -p $BUILD_PATH
    pushd $BUILD_PATH
    git clone git://et.redhat.com/virt-factory
    echo $?
    git clone git://et.redhat.com/koan
    echo $?
    git clone git://et.redhat.com/cobbler
    echo $?
    popd
}

remove_all_packages()
{
    yum remove -y virt-factory-server virt-factory-wui puppet puppet-server virt-factory-register virt-factory-nodes
    echo $?
    # Need to remove koan/cobbler as well
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
    echo $?
}




cleanup_cobbler()
{
    # cobbler changes alot, so blow away any cobbler stuff and reimport it
    CBP="/var/lib/cobbler/"
    rm -rf $CBP/distros $CBP/repos $CBP/profiles $CBP/systems

}

# FIXME: sync this repo
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

stop_services()
{
    /etc/init.d/puppetmaster stop
    /etc/init.d/virt-factory-server stop
    /etc/init.d/virt-factory-wui stop
    /etc/init.d/virt-factory-nodes stop
}

start_services()
{
    /etc/init.d/puppetmaster restart
    /etc/init.d/virt-factory-server restart
    /etc/init.d/virt-factory-wui start
}

start_client_services()
{
    /etc/init.d/puppet start
    /etc/init.d/virt-factory-nodes start
}

register_system()
{
    vf_register --serverurl=$VF_SERVER_URL --username admin --password fedora --profilename $1
    echo $?
}
# commandline parsing
while [ $# -gt 0 ]
do
    case "$1" in
        -h)  help;;
	-r) REBUILD=Y;;
	--rebuild) REBUILD=Y;;
	--checkout) FRESH_CHECKOUT=Y;;
	--sync-repos) SYNC_REPOS=Y;;
	--install-packages) INSTALL_PACKAGES=Y;;
	--skip-packages) INSTALL_PACKAGES=N;;
	--skip-puppet) SETUP_PUPPET=N;;
	--skip-import) VF_SERVER_IMPORT=N;;
	--skip-vf-import) VF_IMPORT=N;;
	--skip-db-refresh) REFRESH_DB=N;;
	--skip-server-start) START_SERVICES=N;;
	--skip-register) REGISTER_SYSTEM=N;;
	--skip-package-remote) REMOVE_PACKAGES=N;;
	--skip-cobbler-cleanup) CLEANUP_COBBLER=N;;
	--cleanup-yum) CLEANUP_YUM=Y;;
    esac
    shift
done

# FIXME: we should probably clone the git repo's then run the script. The script
# thats in the repo. 

stop_services



if [ "$REMOVE_PACKAGES" == "Y" ] ; then
    msg "Removing lots of packages"
    remove_all_packages
    # yum is lame, so we have to do this every time
fi


if [ "$CLEANUP_YUM" == "Y" ] ; then
    msg "Cleaning up the yum caches"
    yum clean all
    #yum clean headers
fi

if [ "$REBUILD" == "Y" ] ; then
    if [ "$FRESH_CHECKOUT" == "Y" ] ; then
	msg "Checking out code from git"
	check_out_code
	# build it all expect us to run it from the source dir, so go
	# there if we need to
	pwd
	pushd $BUILD_PATH/virt-factory/build
    else
	# just so we don't have to track were we are
	pushd `pwd`
    fi
    
    
    msg "Rebuilding everything for kicks in " 

    $BUILD_PATH/virt-factory/build/build-it-all.sh
    
    popd

    # note, we also need to build cobbler and koan, and 
    # add them to the repo. Do we want to do this as part of
    # build-it-all.sh? probably

fi
 
# this syncs the repos to the server, and generates the yum repo.d config files
if [ "$SYNC_REPOS" == "Y" ] ; then
	msg "syncing repos"
	msg "calling sync-it-all.sh with user $REMOTE_USER"
	echo "$BUILD_PATH/virt-factory/build/sync-it-all.py --localpath $BUILD_PATH/virt-factory/build --user $REMOTE_USER --hostname $REMOTE_HOST --path $REMOTE_PATH --release "devel" --distro "fc6" --urlpath $URL_PATH"
	$BUILD_PATH/virt-factory/build/sync-it-all.py --localpath $BUILD_PATH/virt-factory/build --user $REMOTE_USER --hostname $REMOTE_HOST --path $REMOTE_PATH --release "devel" --distro "fc6" --urlpath $URL_PATH

fi


# FIXME: we currently dont rev packages very well, we either need to rev on every package build
# or remove all the packages first, otherwise we never pick up "new, but not newer version" packages
if [ "$INSTALL_PACKAGES" == "Y" ] ; then
    msg "configuring yum"
    cp -av repos.d/* /etc/yum.repos.d/
    
    msg "installing server packages from devel repo"
    install_server_packages

fi


# purge the cobbler setups
if [ "$CLEANUP_COBBLER" == "Y" ] ; then
    msg "Purging the cobbler setup"
    cleanup_cobbler
fi

# purge the db
if [ "$REFRESH_DB" == "Y" ] ; then
    msg "Purging the db"
    rm -rf /var/lib/virt-factory/primary_db
    /usr/bin/vf_create_db.sh
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
    for profile in `ls`
    do
      msg "importing $profile"
      /usr/bin/vf_import $profile
    done
    cd ..
fi

if [ "$START_SERVICES" == "Y" ] ; then
    msg "restarting services"
    start_services
    start_client_services
fi


if [ "$REGISTER_SYSTEM" == "Y" ] ; then
    msg "Registering system"
    register_system $DEFAULT_PROFILE
fi
