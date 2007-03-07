SPEC_FILE	= virtfactory-wui.spec
NAME		= $(shell rpm -q --specfile $(SPEC_FILE) --qf "%{name}\n" | head -1 )
VERSION		= $(shell rpm -q --specfile $(SPEC_FILE) --qf "%{version}\n" | head -1)
NV		= $(NAME)-$(VERSION)
RPM_FLAGS	=	--define "_topdir	%(pwd)" \
			--define "_builddir	%{_topdir}" \
			--define "_rpmdir	%{_topdir}" \
			--define "_srcrpmdir	%{_topdir}" \
			--define '_rpmfilename %%{NAME}-%%{VERSION}-%%{RELEASE}.%%{ARCH}.rpm' \
			--define "_specdir	%{_topdir}" \
			--define "_sourcedir	%{_topdir}"

DATADIR		= $(shell rpm --eval "%{_datadir}")

all: rpm

clean:
	-rm -f virtfactory*.gz virtfactory*.rpm MANIFEST
	-rm -rf virtfactory-wui-* dist build

tar:    clean
	install -d $(NV)
	cp -a src conf $(NV)
	find $(NV) \( -name '*~' -o -name '#*#' \) -print0 | xargs --no-run-if-empty --null rm -vf
	find $(NV)/src/tmp -type f -print0 | xargs --no-run-if-empty --null rm -vf
	tar zcvf $(NV).tar.gz $(NV)
	rm -rf $(NV)

rpm:	tar
	rpmbuild $(RPM_FLAGS) -ba $(SPEC_FILE)
