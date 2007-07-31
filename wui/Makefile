VERSION		= $(shell echo `awk '{ print $$1 }' version`)
RELEASE		= $(shell echo `awk '{ print $$2 }' version`)
NEWRELEASE	= $(shell echo $$(($(RELEASE) + 1)))

SPEC_FILE	= virt-factory-wui.spec
NAME		= virt-factory-wui
 
NV		= $(NAME)-$(VERSION)
RPM_FLAGS	=	--define "_topdir	%(pwd)/rpm-build" \
			--define "_builddir	%{_topdir}" \
			--define "_rpmdir	%{_topdir}" \
			--define "_srcrpmdir	%{_topdir}" \
			--define '_rpmfilename %%{NAME}-%%{VERSION}-%%{RELEASE}.%%{ARCH}.rpm' \
			--define "_specdir	%{_topdir}" \
			--define "_sourcedir	%{_topdir}"

DATADIR		= $(shell rpm --eval "%{_datadir}")

all: rpms

bumprelease:	
	-echo "$(VERSION) $(NEWRELEASE)" > version

setversion: 
	-echo "$(VERSION) $(RELEASE)" > version


clean:
	-rm -f virt-factory*.gz virt-factory*.rpm 
	-rm -rf virt-factory-wui-* dist build

genlangs:
	cd src; rake updatepo; rake makemo

tar: clean genlangs
	mkdir -p $(NV)
	cp -a src conf $(NV)
	find $(NV) \( -name '*~' -o -name '#*#' \) -print0 | xargs --no-run-if-empty --null rm -vf
	find $(NV)/src/tmp -type f -print0 | xargs --no-run-if-empty --null rm -vf
	mkdir -p rpm-build
	tar zcvf rpm-build/$(NV).tar.gz $(NV)
	cp version rpm-build/
	rm -rf $(NV)

new-rpms: bumprelease rpms

rpms: tar	
	rpmbuild $(RPM_FLAGS) -ba $(SPEC_FILE)

# convience method to simulate make install, not for production use
install:
	make rpms
	rpm -Uvh rpm-build/virt-factory-wui-0.0.3-1.fc7.noarch.rpm --force
        /sbin/service virt-factory-wui restart	
