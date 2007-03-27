all: rpms

clean:
	-rm -f  MANIFEST
	-rm -rf dist/ build/
	-rm -rf *~
	-rm -rf rpm-build	
#manpage:
#	pod2man --center="cobbler" --release="" cobbler.pod | gzip -c > cobbler.1.gz
#	pod2html cobbler.pod > cobbler.html

#test:
#	python tests/tests.py
#	-rm -rf /tmp/_cobbler-*

build: clean
	python setup.py build -f

install: build
	python setup.py install -f

sdist: clean
	python setup.py sdist

rpms: sdist
	mkdir -p rpm-build
	cp dist/*.gz rpm-build/
	rpmbuild --define "_topdir %(pwd)/rpm-build" \
	--define "_builddir %{_topdir}" \
	--define "_rpmdir %{_topdir}" \
	--define "_srcrpmdir %{_topdir}" \
	--define '_rpmfilename %%{NAME}-%%{VERSION}-%%{RELEASE}.%%{ARCH}.rpm' \
	--define "_specdir %{_topdir}" \
	--define "_sourcedir  %{_topdir}" \
	-ba virt-factory-register.spec
	
