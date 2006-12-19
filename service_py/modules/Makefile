

FILES           = __init__ config deployment distribution image machine \
		  provisioning registration user  

PYFILES         = $(addsuffix .py, $(FILES))
PYCFILES        = $(addsuffix .pyc, $(FILES))

PYCHECKER       = /usr/bin/pychecker

clean::
	@rm -fv *.pyc *~ .*~ 
	@find . -name .\#\* -exec rm -fv {} \;
	@rm -fv *.rpm

pychecker:: 
	@$(PYCHECKER) $(PYFILES) || exit 0


