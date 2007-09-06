ampm is a commandline client for use with virt-factory, a virtualized guest provisioning
system. 

To use, you need to configure it to use the proper virt-factory server url, username, 
and password. NOTE: these are default values and should be changed.

ampm will read ~/.ampm_config for these values. An example of what this
file looks like is:


[server]
url=http://127.0.0.1:5150
[user]
username=admin
password=fedora


ampm can be used to crete new virt guests, to pause, unpause, stop, shutdown, and
destroy guests.

To see what virt hosts are available:

	% ampm list hosts
        hostname: grimlock.devel.redhat.com id: 1 profile_name: Container::F-7-x86_64


To see what guest profiles are available for creating a guest:

	% ampm list profiles
	Test1::F-7-xen-i386 1.234 F-7-xen-i386
	Test1::F-7-i386 1.234 F-7-i386
	Test1::F-7-x86_64 1.234 F-7-x86_64
	Test1::F-7-xen-x86_64 1.234 F-7-xen-x86_64
	Container::F-7-xen-i386 1 F-7-xen-i386
	Container::F-7-i386 1 F-7-i386
	Container::F-7-x86_64 1 F-7-x86_64
	Container::F-7-xen-x86_64 1 F-7-xen-x86_64


To see what guests are already created:

	% ampm list guests
	(unknown) 00:16:3E:00:00:00 Test1::F-7-x86_64 on host grimlock.devel.redhat.com

To see the list of guests and there current status:

	% ampm list status
	(unknown) 00:16:3E:00:00:00 Test1::F-7-x86_64  on host grimlock.devel.redhat.com is  running


To create a new guest on host (in this case, a KVM guest)
	
	ampm create --host grimlock.devel.redhat.com --profile Test1::F-7-x86_64


To create a new user account on virt-factory:
	ampm add user --username test_user --password test1 --first Robert  --last Belew  --email "bob@example.com" --description "shorttimer"


