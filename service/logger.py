#!/usr/bin/python

import logging

# from the comments in http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/66531
class Singleton(object):
    def __new__(type):
        if not '_the_instance' in type.__dict__:
            type._the_instance = object.__new__(type)
        return type._the_instance

# logging is weird, we don't want to setup mutliple handlers
# so make sure we do that mess only once
class Logger(Singleton):
    __no_handlers = True
    def __init__(self):
        
        self.__setup_logging()
        if self.__no_handlers:
            self.__setup_handlers()
        
    def __setup_logging(self):
        self.logger = logging.getLogger("svc")

    def __setup_handlers(self):
        handler = logging.FileHandler(logfilepath, "a")
        self.logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.__no_handlers = False
