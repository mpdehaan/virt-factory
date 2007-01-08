#!/usr/bin/python


## ShadowManager backend code.
##
## Copyright 2006, Red Hat, Inc
## Michael DeHaan <mdehaan@redhat.com>
## Scott Seago <sseago@redhat.com>
## Adrian Likins <alikins@redhat.com>
##
## This software may be freely redistributed under the terms of the GNU
## general public license.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.


from codes import *
import web_svc

import base64
import os
import time


class Authentication(web_svc.WebSvc):
    tokens = []
    def __init__(self):
        self.methods = {"user_login": self.user_login,
                        "token_check": self.token_check}
        web_svc.WebSvc.__init__(self)

    def user_login(self, username, password):
         """
         Try to log in user with (user,password) and return a token, or raise
         UserInvalidException or PasswordInvalidException on error.
         """
         # this method is the exception to the rule and doesn't do object validation.
         # login is the only special method like this in the whole API.  It's also
         # the only method that doesn't take a hash for a parameter, though this
         # should probably change for consistancy.
         st = """
         SELECT id, password FROM users WHERE username=:username
         """

         if not os.path.exists("/var/lib/shadowmanager/settings"):
             # the app isn't configured.  What this means is that there are (at minimum) no
             # distributions configured and it's basically unusuable.  The WUI here should
             # show a simple splash screen saying the service isn't configured and that the
             # user needs to run two steps on the server.  "shadow init" to create the
             # default config and "shadow import" to import distributions.  Once this is done
             # they will be able to reload and use the WUI,
             raise MisconfiguredException(comment="/var/lib/shadowmanager/settings doesn't exist")

         self.cursor.execute(st, { "username" : username })
         results = self.cursor.fetchone()
         if results is None:
             raise UserInvalidException(comment=username)
         elif results[1] != password:
             raise PasswordInvalidException(comment=username)
         else:
             urandom = open("/dev/urandom")
             token = base64.b64encode(urandom.read(100)) 
             urandom.close()

         self.tokens.append([token, time.time()])
         return success(data=token)

    def token_check(self, token):
        """
        Validate that the token passed in to any method call other than user_login
        is correct, and if not, raise an Exception.  Note that all exceptions are
        caught in dispatch, so methods give failing return codes rather than XMLRPCFaults.
        This is a feature, mainly since Rails (and other language bindings) can better
        grok tracebacks this way.
        """

        
        if not os.path.exists("/var/lib/shadowmanager/settings"):
            x = MisconfiguredException(comment="/var/lib/shadowmanager/settings doesn't exist")
            return x.to_datastruct()

        self.logger.debug("token check, token: %s giventoken: %s" % (self.tokens, token))
        now = time.time()
        for t in self.tokens:
            # remove tokens older than 1/2 hour
            if (now - t[1]) > 1800:
                self.tokens.remove(t)
                return TokenExpiredException().to_datastruct()
            if t[0] == token:
                # update the expiration counter
                t[1] = time.time()
                print "SUCCESS"
                return SuccessException()
                #return success().to_datastruct()
        return TokenInvalidException().to_datastruct()
   


    
    
methods = Authentication()
register_rpc = methods.register_rpc

