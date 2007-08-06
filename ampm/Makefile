RELEASE         = $(shell echo `awk '{ print $$2 }' version`)
NEWRELEASE      = $(shell echo $$(($(RELEASE) + 1)))

all: rpms

bumprelease:    
	-echo "$(VERSION) $(NEWRELEASE)" > version

setversion: 
	-echo "$(VERSION) $(RELEASE)" > version

build: clean
	python setup.py build -f

install: build
	python setup.py install -f

sdist: clean 
	python setup.py sdist



clean::
	@rm -fv *.pyc *~ .*~ 
	@find . -name .\#\* -exec rm -fv {} \;
	@rm -fv *.rpm
	@rm -rfv build/
	@rm -rfv dist/
	@rm -rfv rpm-build/


new-rpms: bumprelease rpms


rpms: sdist
	mkdir -p rpm-build
	cp dist/*.gz rpm-build/
	cp version rpm-build/
	rpmbuild --define "_topdir %(pwd)/rpm-build" \
	--define "_builddir %{_topdir}" \
        --define "_rpmdir %{_topdir}" \
        --define "_srcrpmdir %{_topdir}" \
        --define '_rpmfilename %%{NAME}-%%{VERSION}-%%{RELEASE}.%%{ARCH}.rpm' \
        --define "_specdir %{_topdir}" \
        --define "_sourcedir  %{_topdir}" \
        -ba virt-factory-ampm.spec

