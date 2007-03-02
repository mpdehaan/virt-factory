

clean::
	@rm -fv *.pyc *~ .*~ \#*\# 
#	@find . -name .\#\* -exec rm -fv {} \;
	@rm -fv *.rpm

#eful macro
descend-subdirs = @$(foreach d,$(SUBDIRS), $(MAKE) -C $(d) $@ || exit 1; )

# Now do the same in the subdirs
all clean  :: $(SUBDIRS)
	$(descend-subdirs)

