#/bin/bash

BUILD=`pwd`
SRCDIR="$BUILD/../"
PKGS="register nodes service wui rubypkgstuff"


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
           echo "kaboom"
           exit 1
        fi 
	mv rpm-build/*.src.rpm $BUILD/srpms
	mv rpm-build/*.rpm $BUILD/rpms
	mv rpm-build/*.tar.gz $BUILD/tars
	make clean
        if [ $? != 0 ]; then
           echo "kaboom"
           exit 1
        fi 
done

cd $BUILD

reposync --config=./lutter.repo --repoid=dlutter-fedora --tempcache --download_path=./rpms
reposync --config=./lutter.repo --repoid=dlutter-source --tempcache --download_path=./srpms
mv ./rpms/dlutter-fedora/*.rpm ./rpms/
rm -rf ./rpms/dlutter-fedora
rm -rf ./rpms/repodata

createrepo $BUILD/rpms
createrepo $BUILD/srpms
cd $BUILD/tars
md5sum *.tar.gz > MD5SUMS



