all:
	tar cvf test1-x86_64.tar profile.xml files manifests
	gzip test1-x86_64.tar --force

install:
	vf_import test1-x86_64.tar.gz

clean:
	-rm test1-x86_64.tar.gz
