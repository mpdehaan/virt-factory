all:
	tar cvf container.tar profile.xml files manifests
	gzip container.tar --force

clean:
	-rm container.tar.gz

install:
	vf_import container.tar.gz
