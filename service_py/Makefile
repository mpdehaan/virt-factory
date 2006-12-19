

FILES           = baseobj codes shadow  
SUBDIRS		= modules

PYFILES         = $(addsuffix .py, $(FILES))
PYCFILES        = $(addsuffix .pyc, $(FILES))

PYCHECKER       = /usr/bin/pychecker

clean::
	@rm -fv *.pyc *~ .*~ 
	@find . -name .\#\* -exec rm -fv {} \;
	@rm -fv *.rpm

pychecker:: 
	@$(PYCHECKER) $(PYFILES) || exit 0

#eful macro
descend-subdirs = @$(foreach d,$(SUBDIRS), $(MAKE) -C $(d) $@ || exit 1; )

# Now do the same in the subdirs
all clean install pychecker :: $(SUBDIRS)
	$(descend-subdirs)

