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
	mv rpm-build/*.src.rpm $BUILD/srpms
	mv rpm-build/*.rpm $BUILD/rpms
	mv rpm-build/*.tar.gz $BUILD/tars
	make clean
done

createrepo $BUILD/rpms
createrepo $BUILD/srpms
cd $BUILD/tars
md5sum *.tar.gz > MD5SUMS



