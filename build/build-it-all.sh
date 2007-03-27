#/bin/bash

BUILD=`pwd`
SRCDIR="$BUILD/../"
PKGS="register nodes service wui rubypkgstuff"

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

for i in $PKGS
do
	echo "Building $i"
	cd ../$i
	make rpms 
        if [ $? != 0 ]; then
           echo "kaboom building $i"
           exit 1
        fi 
	mv rpm-build/*.src.rpm $BUILD/srpms
	mv rpm-build/*.rpm $BUILD/rpms
	mv rpm-build/*.tar.gz $BUILD/tars
	make clean
        if [ $? != 0 ]; then
           echo "kaboom cleaning up $i"
           exit 1
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



