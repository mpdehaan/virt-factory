#!/usr/bin/python


import test_case

import os
import sys
import time


sys.path.append("../")
from test_modules import user

class Shadow(object):
    def __init__(self, args=None):
        self.args = args
        self.test_modules = [user]

    def run(self):
        bin = "../shadow.py"

        pid = os.fork()
        if not pid:
            # fork twice to avoid zombies
            pid2 = os.fork()
            if not pid2:
                os.execv("/home/devel/alikins/hg/virt/service/shadow.py", ["shadow.py"])
                # exec -should- never return
                os.perror(_("execv didn't execv?"))
            else:
                # call _exit so we don't mess up filehandles, etc
                os._exit(-1)

    def runtests(self):
        for mod in self.test_modules:
            test_case = mod.testcase()
            test_case.run()
            test_case.report()

    

def main():
    s = Shadow()
#    print s.run()
#    time.sleep(4)
    print s.runtests()
#    print s.report()

if __name__ == "__main__":
    main()
