#/bin/bash

BUILD=`pwd`
SRCDIR="$BUILD/../"
PKGS="register nodes service wui rubypkgstuff"


rm -rf rpms
rm -rf srpms
mkdir -p rpms srpms

for i in $PKGS
do
	echo "Building $i"
	cd ../$i
	make rpms
	mv rpm-build/*.src.rpm $BUILD/srpms
	mv rpm-build/*.rpm $BUILD/rpms
	make clean
done

createrepo $BUILD/rpms
createrepo $BUILD/srpms

