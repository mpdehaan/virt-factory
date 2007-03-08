#!/usr/bin/python


import distutils.sysconfig
import os
import sys
import glob


module_path="%s/virt-factory/nodes/" % distutils.sysconfig.get_python_lib()
sys.path.append(module_path)


def load_modules(module_path, blacklist=None):
    filenames = glob.glob("%s/*.py" % module_path)
    filenames = filenames + glob.glob("%s/*.pyc" % module_path)
    filesnames = filenames + glob.glob("%s.*.pyo" % module_path)

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
            print "%s/%s" % (module_path, modname)
            blip =  __import__("%s/%s" % (module_path, modname))
            if not hasattr(blip, "register_rpc"):
                print "%s/%s module not a proper module" % (module_path, modname) 
                continue
            mods[modname] = blip
        except ImportError, e:
            print e

    return mods




if __name__ == "__main__":
    print load_modules(module_path)

    
