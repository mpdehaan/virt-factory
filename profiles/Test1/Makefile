VERSION		= $(shell echo `awk '{ print $$2 }' version`)
RELEASE		= $(shell echo `awk '{ print $$3 }' version`)
NEWRELEASE	= $(shell echo $$(($(RELEASE) + 1)))
PROFILE		= $(shell echo `awk '{ print $$1 }' version`)

SPEC_FILE	= vf-profile-$(PROFILE).spec
NAME		= vf-profile-$(PROFILE)
 
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
	-echo "$(PROFILE) $(VERSION) $(NEWRELEASE)" > version

setversion: 
	-echo "$(PROFILE) $(VERSION) $(RELEASE)" > version


clean:
	-rm -f vf-profile*.gz vf-profile*.rpm 
	-rm -rf vf-profile-${NAME}-* dist build


tar:    clean
	mkdir -p $(NV)
	mkdir -p manifests
	mkdir -p files
	mkdir -p templates
	cp -a profile.xml manifests files templates $(NV)
	find $(NV) \( -name '*~' -o -name '#*#' \) -print0 | xargs --no-run-if-empty --null rm -vf
	mkdir -p rpm-build
	tar zcvf rpm-build/$(NV).tar.gz $(NV)
	cp version rpm-build/
	rm -rf $(NV)

new-rpms: bumprelease rpms

rpms: tar	
	rpmbuild $(RPM_FLAGS) -ba $(SPEC_FILE)
