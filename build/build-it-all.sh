#/bin/bash

BUILD=`pwd`
SRCDIR="$BUILD/../"
VF_PKGS="common/busrpc register nodes service wui rubypkgstuff"
COBBLER_PKGS="cobbler koan"


if [ ! -f "/usr/bin/createrepo" ]; then
	echo "you need createrepo installed"
	exit 1
fi

if [ ! -f "/usr/bin/reposync" ] ; then
	echo "you need yum-utils installed (for reposync)"
	exit 1
fi

rm -rf rpms
rm -rf srpms
rm -rf tars
mkdir -p rpms srpms tars

build_rpm()
{
    PKG=$1
    BRT=$2
    echo;echo;echo
    echo "======================================"
    echo "Building $PKG"
    echo "======================================"
    echo
    cd $2/$PKG
    make rpms 
    if [ $? != 0 ]; then
	echo "kaboom building $PKG"
	exit 1
    fi 
    mv rpm-build/*.src.rpm $BUILD/srpms
    mv rpm-build/*.rpm $BUILD/rpms
    mv rpm-build/*.tar.gz $BUILD/tars
    make clean
    if [ $? != 0 ]; then
	echo "kaboom cleaning up $PKG"
	exit 1
    fi 
}

for i in $VF_PKGS
do
  build_rpm $i $SRCDIR
done



# FIXME: we probably need to build cobbler/koan as well
# FIXME: cobbler/koan use different build stuff

build_profile()
{
    PROFILE=$1
    pwd
    echo "Building the profile for $PROFILE" 
    pushd $PROFILE
    make
    mkdir -p $BUILD/profiles
    cp *.tar.gz $BUILD/profiles/
    popd
}

# build all the latest profiles
cd $SRCDIR
pwd
cd profiles
ls *
for i in `ls`
do
  build_profile $i
done

# build cobbler and koan
# we need to have these in a parallel checkout

CK_SRCDIR="$SRCDIR/../"
ls $CK_SRCDIR
ls $CK_SRCDIR/cobbler

for i in $COBBLER_PKGS
do
  echo "======= building $i ========"
  if [ -d "$CK_SRCDIR/$i" ] ; then
      pushd $CK_SRCDIR
      build_rpm $i $CK_SRCDIR
  fi
done


cd $BUILD

reposync --config=./lutter.repo --repoid=dlutter-fedora  --download_path=./rpms
reposync --config=./lutter.repo --repoid=dlutter-source  --download_path=./srpms
mv ./rpms/dlutter-fedora/*.rpm ./rpms/
rm -rf ./rpms/dlutter-fedora
rm -rf ./rpms/repodata

createrepo $BUILD/rpms
createrepo $BUILD/srpms
cd $BUILD/tars
md5sum *.tar.gz > MD5SUMS



