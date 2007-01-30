#!/usr/bin/python


import os
import sys
import glob


module_path="modules/"
sys.path.append(module_path)

def load_modules(module_path, blacklist=None):
    filenames = glob.glob("%s/*.py" % module_path)
    filenames = filenames + glob.glob("%s/*.pyc" % module_path)
    filesnames = filenames + glob.glob("%s.*.pyo" % module_path)

    mods = {}

#    print "filenames", filenames
    for fn in filenames:
        basename = os.path.basename(fn)
        if basename[-3:] == ".py":
            modname = basename[:-3]
        elif basename[-4:] in [".pyc", ".pyo"]:
            modname = basename[:-4]

        try:
            blip =  __import__("%s/%s" % (module_path, modname))
            mods[modname] = blip
        except ImportError, e:
            print e

    return mods




if __name__ == "__main__":
    print load_modules(module_path)

    
