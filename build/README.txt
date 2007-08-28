stuff you need to run test-it-all.sh

A machine running f7
a test-it-call.conf tailored to your setup
	(running test-it-all.sh will start by dumping all the available
	config options to stdout, for C&P ease)

For the default settings, you need /mnt/engarchive2 setup
make sure /etc/auto.mnt has a line like:
engarchive2 -defaults,async,intr,noatime,nodev,nosuid,nfsvers=3,rsize=8192,wsize=8192,ro engarchive.rdu.redhat.com:/engineering/archives2

and that autofs is running

/var/www/html needs to be writeable by whatever user test-it-all.conf says to
use for remote sync


Firewall needs to let out at least 80, 5150, 2112. easiest just to disable it.
Turning off selinux wouldn't hurt. 

make sure libvirtd is running

See https://hosted.fedoraproject.org/projects/cobbler/wiki/VirtNetworkingSetupForUseWithKoan
for bridge networking setup.


you need to apply the patch here:
https://www.redhat.com/archives/et-mgmt-tools/2007-August/msg00045.html
to virtinstal if you want anything useful to happen when you do an install





httpd
kvm
qemu
xen
ruby-devel
ruby-gettext-package
ruby-rake
ruby-rake-gem
ruby
createrepo
yum-utils
python-devel
python-setuptools
rpm-build
postgresql
