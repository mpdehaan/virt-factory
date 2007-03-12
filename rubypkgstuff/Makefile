specs = $(wildcard *.spec)

rpms:	clean $(specs)

empty: ;

clean:
	rm -f *.rpm

%.spec: empty
	rpmbuild --define "_topdir %(pwd)" \
	--define "_builddir %{_topdir}" \
	--define "_rpmdir %{_topdir}" \
	--define "_srcrpmdir %{_topdir}" \
	--define '_rpmfilename %%{NAME}-%%{VERSION}-%%{RELEASE}.%%{ARCH}.rpm' \
	--define "_specdir %{_topdir}" \
	--define "_sourcedir  %{_topdir}" \
	-ba $@
