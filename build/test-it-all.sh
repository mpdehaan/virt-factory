#!/bin/bash


help()
{
	echo "no help yet"
}


install_packages()
{
	yum install -y virt-factory-server virt-factory-client virt-factory-register virt-factory-wui puppet puppet-server
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
REMOTE_PATH="/var/www/html/download"
URL_PATH="/download/"


# er, variables...
REBUILD=N
SYNC_REPOS=N
INSTALL_PACKAGES=Y
SETUP_PUPPET=Y
VF_SERVER_IMPORT=N
VF_IMPORT=Y
REFRESH_DB=Y

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
    esac
    shift
done


if [ "$REBUILD" == "Y" ] ; then
	echo "Rebuilding everything for kicks"
	./build-it-all.sh
fi
 
# this syncs the repos to the server, and generates the yum repo.d config files
if [ "$SYNC_REPOS" == "Y" ] ; then
	echo "syncing repos"
	echo "calling sync-it-all.sh with user $REMOTE_USER"
	./sync-it-all.py --user $REMOTE_USER --hostname $REMOTE_HOST --path $REMOTE_PATH --release "devel" --distro "fc6" --urlpath $URL_PATH

fi

if [ "$REFRESH_DB" == "Y" ] ; then
    echo "Purging the db"
    rm -rf /var/lib/virt-factory/primary_db
    /usr/bin/vf_create_db.sh
fi

if [ "$INSTALL_PACKAGES" == "Y" ] ; then
        echo "configuring yum"
	cp -av repos.d/* /etc/yum.repos.d/

	echo "installing packages"
        install_packages
fi

if [ "$SETUP_PUPPET" == "Y" ] ; then
	echo "Setting up puppet"
	setup_puppet
fi


if [ "$VF_SERVER_IMPORT" == "Y" ] ; then
	echo "Starting vf_server import, this could take a while"
	/usr/bin/vf_server import
fi


if [ "$VF_IMPORT" == "Y" ] ; then
    echo "importing profiles"
    cd profiles/
    for profile in `cat profile_manifest`
    do
      echo "importing $profile"
      /usr/bin/vf_import $profile
    done
    cd ..
fi

