#!/bin/bash


#REMOTE_USER=$USER

# note, the user you log in as needs perms to write to 
# REMOTE_PATH 
REMOTE_USER="mdehaan"
# This is the machine we rsync the yum repos to, and 
# setup the repo files to point at
REMOTE_HOST="mdehaan.rdu.redhat.com"
REMOTE_PATH="/var/www/html/download"
URL_PATH="/download/"

# the profile we assign to a system on registration
DEFAULT_PROFILE="Container"

# where we checkout the code to, and run the build
BUILD_PATH="/tmp/vf-test"

# this will be the local machines ip of the interface
# that the code will be running on
VF_SERVER="http://172.16.59.215"

ARCH="f7"

VIRSH_CONNECTION="--connect qemu:///system"

# er, variables...

# this does a rebuild of all the packages
REBUILD=Y

# check out a clean copy from git
FRESH_CHECKOUT=Y

# run sync-it-all to sync the repo's we build to a remote machine 
SYNC_REPOS=Y

# do we install new package of all the code we built (we do this with
# yum from the repos we sync
INSTALL_PACKAGES=Y

# FIXME: I think this can go away actually...
SETUP_PUPPET=Y

# run 'vf_server import` to setup cobbler
VF_SERVER_IMPORT=Y

# run vf_import on the profiles in the repo
VF_IMPORT=Y

# backup existing db to db_backup/, delete the old one, and recreate a new one
REFRESH_DB=Y

# startup all the various daemons
START_SERVICES=Y

# register the local box
REGISTER_SYSTEM=Y

# remove the old virt-factory related packages
REMOVE_PACKAGES=Y

# remove any existing cobbler setups
CLEANUP_COBBLER=Y

# run yum clean all
# FIXME: this is a workaround to packages not getting
# versioned properly
CLEANUP_YUM=Y

# remove any existing puppet configs/certs/etc
CLEANUP_PUPPET=Y

# do some basic testing of the wui code
TEST_WEB_STUFF=Y


# try to run nodecomm to see if basic ssl stuff is working
TEST_NODECOMM=Y

# do we try doing an actual deployment
TEST_PROFILE_DEPLOY=Y
# where to deploy?
DEPLOY_HOST=mdehaan.rdu.redhat.com

# which profile to deploy in the test deploy
TEST_PROFILE="Test1::F-7-x86_64"

# whether to attempt to slay and undefine the first virtual
# machine prior to starting testing, otherwise, testing
# a deployment will fail.
DEPLOY_DESTROY=Y

# whether or not we test the ampm commandline client
TEST_AMPM=Y

# you can put conf stuff in test-it-all.conf 
# so you don't have to worry about checking in config stuff
if [ -f "test-it-all.conf" ] ; then
    source test-it-all.conf
fi


# since we can change VF_SERVER in the config, expand this after that
VF_SERVER_URL="$VF_SERVER"

COOKIES_FILE="cookies"

show_config()
{
    echo "REMOTE_USER=$REMOTE_USER"
    echo "REMOTE_HOST=$REMOTE_HOST"
    echo "REMOTE_PATH=$REMOTE_PATH"
    echo "URL_PATH=$URL_PATH"
   
    echo "DEFAULT_PROFILE=$DEFAULT_PROFILE"
    echo "BUILD_PATH=$BUILD_PATH"
    echo "VF_SERVER=$VF_SERVER"

    echo "REBUILD=$REBUILD"
    echo "FRESH_CHECKOUT=$FRESH_CHECKOUT"
    echo "SYNC_REPOS=$SYNC_REPOS"
    echo "INSTALL_PACKAGES=$INSTALL_PACKAGES"
    echo "SETUP_PUPPET=$SETUP_PUPPET"
    echo "VF_SERVER_IMPORT=$VF_SERVER_IMPORT"
    echo "VF_IMPORT=$VF_IMPORT"
    echo "REFRESH_DB=$REFRESH_DB"
    echo "START_SERVICES=$START_SERVICES"
    echo "REGISTER_SYSTEM=$REGISTER_SYSTEM"
    echo "REMOVE_PACKAGES=$REMOVE_PACKAGES"
    echo "CLEANUP_COBBLER=$CLEANUP_COBBLER"
    echo "CLEANUP_YUM=$CLEANUP_YUM"
    echo "CLEANUP_PUPPET=$CLEANUP_PUPPET"
    echo "TEST_WEB_STUFF=$TEST_WEB_STUFF"
    echo "TEST_NODECOMM=$TEST_NODECOMM"
    echo "TEST_PROFILE_DEPLOY=$TEST_PROFILE_DEPLOY"
    echo "TEST_PROFILE=$TEST_PROFILE"
    echo "TEST_AMPM=$TEST_AMPM"
    echo "DEPLOY_DESTROY=$DEPLOY_DESTROY"
    echo "ARCH=$ARCH"
    echo "VIRSH_CONNECTION=$VIRSH_CONNECTION"
}

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
    echo "Build path is $BUILD_PATH"
    rm -rf $BUILD_PATH
    mkdir -p $BUILD_PATH
    pushd $BUILD_PATH
    git clone git://et.redhat.com/virt-factory
    echo $?
    git clone git://git.fedoraproject.org/git/hosted/cobbler 
    echo $?
    git clone git://git.fedoraproject.org/git/hosted/koan
    echo $?
    popd
}

remove_virtual_machine()
{
    virsh $VIRSH_CONNECTION destroy 00_16_3E_00_00_00
    virsh $VIRSH_CONNECTION destroy 00_16_3E_00_00_01
    virsh $VIRSH_CONNECTION destroy 00_16_3E_00_00_02
    virsh $VIRSH_CONNECTION destroy 00_16_3E_00_00_03
    virsh $VIRSH_CONNECTION undefine 00_16_3E_00_00_00
    virsh $VIRSH_CONNECTION undefine 00_16_3E_00_00_01
    virsh $VIRSH_CONNECTION undefine 00_16_3E_00_00_02
    virsh $VIRSH_CONNECTION undefine 00_16_3E_00_00_03
}

remove_all_packages()
{
    rm /etc/virt-factory/db/exists
    yum remove -y python-migrate virt-factory-server virt-factory-wui puppet puppet-server virt-factory-register \
		  virt-factory-nodes koan cobbler rubygem-mongrel rubygem-rails postgresql-server \
		  python-psycopg2 postgresql-python python-sqlalchemy amqp python-qpid qpidd qpidc virt-factory-ampm
    echo $?
}


# packages needed for the virt-factory server itself
install_server_packages()
{
    yum install -y virt-factory-server  virt-factory-wui virt-factory-ampm puppet puppet-server cobbler 
}


# packages needed for a node machine
# note, for this test, the machine running this script will install the server and the client code
install_client_packages()
{
    yum install -y virt-factory-nodes virt-factory-register virt-factory-ampm koan puppet 
    echo $?
}




cleanup_cobbler()
{
    # cobbler changes alot, so blow away any cobbler stuff and reimport it
    CBP="/var/lib/cobbler/"
    rm -rf $CBP/distros $CBP/repos $CBP/profiles $CBP/systems

}

cleanup_repo_mirror()
{

    rm -rf /var/www/cobbler/repo_mirror/*
}


cleanup_puppet()
{
    # blow away any puppet configs that might be about
    rm -rf /var/lib/puppet/*
} 

# FIXME: sync this repo
# create the repo like the one at 
# http://virt-factory.et.redhat.com/download/repo/$ARCH/stable/i386/
# but with the recently built packages and synced to REMOTE_HOST so
# that the vf_server import/cobbler import can be told to sync it from there
# and create the virt-factory vf_repo repo 
setup_vf_repo_upstream()
{
    msg "setup_vf_repo_upstream"

}

# note, in this function, the DB and server probably aren't started yet
setup_vf_server()
{
    msg "Setting up the config settings for vf_server"
 
    HN=`hostname`
    # FIXME: were just reposyncing the normal repo to a specific path
    # FIXME: this path shouldn't be hardcoded
    get_fedora_release
    ARCH=`uname -p`
    VF_REPO="http://$REMOTE_HOST/$URL_PATH"
    cp settings settings.testing
    export HN VF_REPO
    perl -p -i -e "s/ADDRESS/\$ENV{'HN'}/g" settings.testing
    perl -p -i -e "s/VF_REPO/\$ENV{'VF_REPO'}/g" settings.testing
    cp -f settings.testing /etc/virt-factory/settings
}

setup_puppet()
{
    # FIXME: can this be removed?
    touch /etc/puppet/manifests/site.pp
}

stop_services()
{
    /etc/init.d/iptables stop
    /etc/init.d/cobblerd stop
    /etc/init.d/puppetmaster stop
    /etc/init.d/virt-factory-server stop
    /etc/init.d/virt-factory-wui stop
    /etc/init.d/virt-factory-node-server stop
    /etc/init.d/postgresql stop
}

start_services()
{
    /etc/init.d/cobblerd start
    /etc/init.d/puppetmaster restart
    /etc/init.d/qpidd restart
    

    # for someone reason f7 doesn't do the initdb on startup
    if [ "$FEDORA_RELEASE" == "7" ] ; then
	/etc/init.d/postgresql initdb
    fi

    # just to be sure...
    /etc/init.d/postgresql start
    
    # this will restart postgresql
    # and also set up it's pg_hba.conf
    vf_fix_db_auth

    /etc/init.d/virt-factory-server restart
    /etc/init.d/virt-factory-wui restart
    
    # we need to restart httpd after installing mongrel
    /etc/init.d/httpd restart

    /etc/init.d/libvirtd restart
}

start_client_services()
{
    /etc/init.d/puppet start
    /etc/init.d/virt-factory-node-server start
}

register_system()
{
    echo "vf_register --serverurl=$VF_SERVER_URL --username admin --password fedora --profilename $1"
    vf_register --serverurl=$VF_SERVER_URL --username admin --password fedora --profilename $1
    echo $?
}


get_fedora_release()
{
    FEDORA_RELEASE=`rpm -q --queryformat "%{VERSION}\n" fedora-release`
}

web_login()
{
    echo "logging into login page of $VF_SERVER"
    curl -s -L -o output  -b $COOKIES_FILE -c $COOKIES_FILE  -d "form[username]=admin&form[password]=fedora&submit='Log In'" $VF_SERVER/vf/login/submit
}

test_web_stuff()
{
    msg "Hitting the web site for some basic testing"
    web_login
    LIST_OF_URL_PATHS="/profile/list /user/list /machine/list /deployment/list /task/list /machine/edit /regtoken/edit /regtoken/list /deployment/list /user/edit /profile/edit/0 /machine/edit/0 /user/edit/1"
    for path in $LIST_OF_URL_PATHS 
    do
	echo "testing $VF_SERVER/vf/$path" 
	RET_CODE=`curl -L -b $COOKIES_FILE -c $COOKIES_FILE -o output_file -w "%{http_code}\n" -s $VF_SERVER/vf/$path`
	if [ "$RET_CODE" != "200" ] ; then
	    echo "$VF_SERVER/vf/$path returned an error code of $RET_CODE"
	fi
    done
}


deploy_a_system_web()
{

    # FIXME: this is a bit hardcode at
    web_login
    echo curl  -s -w "%{http_code}\n" -L  -b $COOKIES_FILE -c $COOKIES_FILE  -d "form[machine_id]='1'&form[profile_id]=2&form[puppet_node_diff]=&submit='Add'" http://$DEPLOY_HOST/vf/deployment/edit_submit
    RET_CODE=`curl  -s -w "%{http_code}\n" -L  -b $COOKIES_FILE -c $COOKIES_FILE  -d "form[machine_id]=1&form[profile_id]=2&form[puppet_node_diff]=&submit='Add'" http://$DEPLOY_HOST/vf/deployment/edit_submit`
    echo "Provisioning a system returned $RET_CODE"


}

# use ampm to do the test deploy, since it's easier than trying to talk to the wui,
# which is the whole point of ampm, afterall
deploy_a_system()
{
    msg "Deploying a $TEST_PROFILE on DEPLOY_HOST"
    /usr/bin/ampm create --host $DEPLOY_HOST --profile "$TEST_PROFILE"

}

test_nodecomm()
{
    msg "Testing vf_nodecomm to see if basic node stuff is working"
    HN=`hostname`
    /usr/bin/vf_nodecomm $HN $HN $HN test_add 1 2 
    echo $?
    rm /tmp/blippy
    /usr/bin/vf_nodecomm $HN $HN $HN test_blippy 52.8
    if ! [ -f /tmp/blippy ]; then
       echo "test_blippy failed"
    fi
}



test_ampm()
{
    sh ampm-it-all.sh

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
	--skip-puppet-cleanup) CLEANUP_PUPPET=N;;
	--cleanup-yum) CLEANUP_YUM=Y;;
	--skip-web-test) TEST_WEB_STUFF=N;;
	--skip-nodecomm-test) TEST_NODECOMM=N;;
	--skip-profile-deploy) TEST_PROFILE_DEPLOY=N;;
    esac
    shift
done

# FIXME: we should probably clone the git repo's then run the script. The script
# thats in the repo. 

show_config

# if stuffs not running, this might gripe
stop_services


if [ "$DEPLOY_DESTROY" == "Y" ] ; then
    msg "Destroying first allocated virtual machine"
    remove_virtual_machine
fi

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
	msg "!!! Skipping checkout"
        pushd `pwd`
    fi
    
    
    msg "Rebuilding everything for kicks in $BUILD_PATH" 

    $BUILD_PATH/virt-factory/build/build-it-all.sh
   
    if [ $? != 0 ]; then
        echo "Error building packages"
        exit 1
    fi
 
    popd

fi
 
# this syncs the repos to the server, and generates the yum repo.d config files
if [ "$SYNC_REPOS" == "Y" ] ; then
	# deal with stale packages -- this may very well be wrong
        msg "syncing repos"
	msg "calling sync-it-all.sh with user $REMOTE_USER"
	BUILD_ARCH=`uname -p`
	get_fedora_release
	BUILD_RELEASE=$FEDORA_RELEASE
        ssh $REMOTE_USER@$REMOTE_HOST rm -rf /var/www/html/download/*
        
	echo "$BUILD_PATH/virt-factory/build/sync-it-all.py --localpath $BUILD_PATH/virt-factory/build --user $REMOTE_USER --hostname $REMOTE_HOST --path $REMOTE_PATH --release devel --distro f$FEDORA_RELEASE --arch $BUILD_ARCH --urlpath $URL_PATH"
	$BUILD_PATH/virt-factory/build/sync-it-all.py --localpath $BUILD_PATH/virt-factory/build --user $REMOTE_USER --hostname $REMOTE_HOST --path $REMOTE_PATH --release "devel" --distro "f$FEDORA_RELEASE" --arch "$BUILD_ARCH" --urlpath $URL_PATH
	echo "ssh $REMOTE_USER@$REMOTE_HOST ln -s /var/www/html/download/repo/$ARCH/devel/i686 /var/www/html/download/repo/$ARCH/devel/i386"
        ssh $REMOTE_USER@$REMOTE_HOST ln -s /var/www/html/download/repo/$ARCH/devel/i686 /var/www/html/download/repo/$ARCH/devel/i386
fi

# purge the db
if [ "$REFRESH_DB" == "Y" ] ; then
    msg "Purging the db"
    mkdir -p db_backup
    TIMESTAMP=` date '+%s'`
    mv /var/lib/psql "db_backup/"
    rm -rf /var/lib/pgsql
    rm -rf /etc/virt-factory/db
fi

# FIXME: we currently dont rev packages very well, we either need to rev on every package build
# or remove all the packages first, otherwise we never pick up "new, but not newer version" packages
if [ "$INSTALL_PACKAGES" == "Y" ] ; then
    msg "configuring yum"
    cp -av repos.d/* /etc/yum.repos.d/


    # I'm not entirely sure why we need this here, but otherwise yum complains
    # about bogus stuff in the cache, despite having done a clean all just a few
    # steps above
    if [ "$CLEANUP_YUM" == "Y" ] ; then
	msg "Cleaning up the yum caches"
	yum clean all
    #yum clean headers
    fi
    
    msg "installing server packages from devel repo"
    install_server_packages

fi


# purge the cobbler setups
if [ "$CLEANUP_COBBLER" == "Y" ] ; then
    msg "Purging the cobbler setup"
    cleanup_cobbler
fi

if [ "$CLEANUP_PUPPET" == "Y" ] ; then
    msg "Cleaning up puppet configs"
    cleanup_puppet
fi

if [ "$SETUP_PUPPET" == "Y" ] ; then
    msg "Setting up puppet"
    setup_puppet
fi

# do the config tweaking for the local vf_server
setup_vf_server 

# lets try cleaning up the cobbler repos
msg "cleanup repo mirror"
cleanup_repo_mirror

# NOTE: we have to do this after "vf_server import" as that creates
# the vf_repo
if [ "$INSTALL_PACKAGES" == "Y" ] ; then
    msg "Installing client packages from vf_repo"
    install_client_packages
fi

if [ "$START_SERVICES" == "Y" ] ; then
    msg "restarting services"
    start_services
    start_client_services
fi

# This creates the vf_repo as well, though we probably need to create the sample
# repo somewhere ($REMOTE_HOST?) and set the settings to sync from there to here,
# so that we get the fresh packages we just built
if [ "$VF_SERVER_IMPORT" == "Y" ] ; then
    msg "Starting vf_server import, this could take a while"
   
    # do the rynsc, the db import, and reposync the vf_repo's
    /usr/bin/vf_server import
fi


if [ "$VF_IMPORT" == "Y" ] ; then
    msg "importing profiles"

    # import the profiles from the checkout tree
    PROFILE_DIR="/profiles"
    if [ "$REBUILD" == "Y" ] ; then
	PROFILE_DIR="$BUILD_PATH/virt-factory/build/profiles"
    fi

    pushd $PROFILE_DIR
    for profile in `ls`
    do
      msg "importing $profile"
      rpm -Uvh $profile --force
    done
    /usr/bin/vf_import
    popd
fi

if [ "$REGISTER_SYSTEM" == "Y" ] ; then
    msg "Registering system"
    register_system $DEFAULT_PROFILE
fi

if [ "$TEST_WEB_STUFF" == "Y" ] ; then
    msg "Running some basic tests on the web interface"
    test_web_stuff
fi

if [ "$TEST_NODECOMM" == "Y" ] ; then
    msg "Running some basic nodecomm tests"
    test_nodecomm
fi



if [ "$TEST_AMPM" == "Y" ] ; then
    msg "Testing ampm"
    test_ampm
fi

if [ "$TEST_PROFILE_DEPLOY" == "Y" ] ; then
    msg "Running a virtual system deployment"
    deploy_a_system
fi

