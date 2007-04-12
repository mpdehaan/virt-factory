all:
	tar cvf test1.tar profile.xml files manifests
	gzip test1.tar --force

install:
	vf_import test1.tar.gz

clean:
	-rm test1.tar.gz
