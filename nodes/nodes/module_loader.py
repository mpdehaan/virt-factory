#!/usr/bin/python


import distutils.sysconfig
import os
import sys
import glob


module_file_path="%s/virt-factory/nodes/modules" % distutils.sysconfig.get_python_lib()
mod_path="%s/virt-factory/nodes/" % distutils.sysconfig.get_python_lib()
sys.path.insert(0, mod_path)

def load_modules(module_path=module_file_path, blacklist=None):
    filenames = glob.glob("%s/*.py" % module_file_path)
    filenames = filenames + glob.glob("%s/*.pyc" % module_file_path)
    filesnames = filenames + glob.glob("%s/*.pyo" % module_file_path)

    mods = {}

    for fn in filenames:
        basename = os.path.basename(fn)
        if basename == "__init__.py":
            continue
        if basename[-3:] == ".py":
            modname = basename[:-3]
        elif basename[-4:] in [".pyc", ".pyo"]:
            modname = basename[:-4]

        
        try:
            blip =  __import__("nodes.modules.%s" % ( modname), globals(), locals(), [modname])
            if not hasattr(blip, "register_rpc"):
                print "%s/%s module not a proper module" % (module_path, modname) 
                continue
            mods[modname] = blip
        except ImportError, e:
            print e

    return mods




if __name__ == "__main__":
    print load_modules(module_path)

    
