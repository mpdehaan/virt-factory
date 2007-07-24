#!/usr/bin/python


import distutils.sysconfig
import os
import sys
import glob
from rhpl.translate import _, N_, textdomain, utf8

module_file_path="modules/"
#mod_path="%s/virt-factory/nodes/" % distutils.sysconfig.get_python_lib()
#sys.path.insert(0, mod_path)

def load_modules(module_path=module_file_path, blacklist=None):
#    if module_path not in sys.path:
#        sys.path.insert(0, module_path)
    filenames = glob.glob("%s/*.py" % module_path)
#    filenames = filenames + glob.glob("%s/*.pyc" % module_path)
#    filesnames = filenames + glob.glob("%s/*.pyo" % module_path)

    mods = {}

    print sys.path
    print "filenames", filenames
    print

    
    for fn in filenames:
        basename = os.path.basename(fn)
        if basename == "__init__.py":
            continue
        if basename[-3:] == ".py":
            modname = basename[:-3]
        elif basename[-4:] in [".pyc", ".pyo"]:
            modname = basename[:-4]

        print "modname:", modname
        try:
            blip =  __import__("modules.%s" % ( modname), globals(), locals(), [modname])
            if not hasattr(blip, "register_rpc"):
		errmsg = _("%(module_path)s/%(modname)s module not a proper module")
                print errmsg % {'module_path': module_path, 'modname':modname} 
                continue
            mods[modname] = blip
        except ImportError, e:
            print e

    return mods




if __name__ == "__main__":
    print load_modules(module_file_path)

    
