#!/bin/bash


help()
{
	echo "no help yet"
}


install_packages()
{
	yum install virt-factory-server virt-factory-client virt-factory-register virt-factory-wui puppet puppet-server
}



setup_puppet()
{
	touch /etc/puppet/manifests/site.pp
	host=`hostname`
	perl -p -i -e 's/SUBSTITUTE_ME/$host/g' settings.testing
	cp -f settings.testing /etc/virt-factory/settings

}

#REMOTE_USER=$USER
REMOTE_USER="alikins"
REMOTE_HOST="grimlock.devel.redhat.com"
REMOTE_PATH="/tmp/html/yum/"


# er, variables...
REBUILD=N
SYNC_REPOS=N
INSTALL_PACKAGES=Y
SETUP_PUPPET=Y

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
    esac
    shift
done


if [ "$REBUILD" == "Y" ] ; then
	echo "Rebuilding everything for kicks"
	./build-it-all.sh
fi

if [ "$SYNC_REPOS" == "Y" ] ; then
	echo "syncing repos"
	echo "calling sync-it-all.sh with user $REMOTE_USER"
	./sync-it-all.py --user $REMOTE_USER --hostname $REMOTE_HOST --path $REMOTE_PATH --release "devel" --distro "fc6"

fi

if [ "$INSTALL_PACKAGES" == "Y" ] ; then
	echo "installing packages"
	# install_packages
fi

if [ "$SETUP_PUPPET" == "Y" ] ; then
	echo "Setting up puppet"
	setup_puppet
fi

