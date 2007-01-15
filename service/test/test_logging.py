#!/usr/bin/python



import logging



logger = logging.getLogger("test")
handler = logging.FileHandler("/tmp/foobar", "a")
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.debug("this is a debug")
logger.warn("this is a warn")
logger.info("this is an info")
