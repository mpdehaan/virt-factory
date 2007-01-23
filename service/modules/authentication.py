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
import threading
import time

SESSION_LENGTH=200

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

         if not os.path.exists("/var/lib/shadowmanager/primary_db"):
             raise MisconfiguredException(comment="/var/lib/shadowmanager/primary_db doesn't exist")

         self.db.cursor.execute(st, { "username" : username })
         results = self.db.cursor.fetchone()
         if results is None:
             raise UserInvalidException(comment=username)
         elif results[1] != password:
             raise PasswordInvalidException(comment=username)

         user_id = results[0]
         urandom = open("/dev/urandom")
         token = base64.b64encode(urandom.read(100)) 
         urandom.close()

         #cleanup old sessions
         self.__cleanup_old_sessions_by_userid(user_id)
         

         st = """
         INSERT INTO sessions (
                     session_token,
                     user_id, 
                     session_timestamp)
                VALUES (
                     :session,
                     :user_id,
                     :timestamp)
                     """

         #"
         lock = threading.Lock()
         lock.acquire()
         try:
             self.db.cursor.execute(st, {"session": token,
                                         "user_id": user_id,
                                         "timestamp": time.time()} )
             self.db.connection.commit()
         except Exception, e:
             # FIXME: we also need to check just in case we collide on the
             # session token. Cause you know, the chances of hitting a collision
             # in a 100 byte random blob is much higher than me screwing up
             # any other bugs.
             
             # FIXME: be more fined grained (IntegrityError only)
             lock.release()
             raise SQLException(traceback=traceback.format_exc())

         lock.release()
         return success(data=token)


    def _cleanup_old_sessions(self):
        """
        Delete any old sessions 
        """
        
        st = """
        DELETE FROM
               sessions
        WHERE
               session_timestamp < :timestamp
        """

         
        lock = threading.Lock()
        lock.acquire()
        try:
            self.db.cursor.execute(st, {"timestamp": (time.time() - SESSION_LENGTH)} )
            self.db.connection.commit()
        except:
            lock.release()
            raise SQLException(traceback=traceback.format_exc())
        lock.release()

    def __cleanup_old_sessions_by_userid(self, user_id):
        """
        Delete any old sessions owned bt this user
        """
        
        st = """
        DELETE FROM
               sessions
        WHERE
               user_id=:user_id and
               session_timestamp < :timestamp
        """

         
        lock = threading.Lock()
        lock.acquire()
        try:
            self.db.cursor.execute(st, {"user_id": user_id,
                                        "timestamp": (time.time() - SESSION_LENGTH)} )
            self.db.connection.commit()
        except:
            lock.release()
            raise SQLException(traceback=traceback.format_exc())
        lock.release()

         


    def __delete_session(self, session_token):
        """
        The session has expired, delete it from the db
        """
        st = """
        DELETE FROM sessions
        WHERE session_token = :session_token
        """

        lock = threading.Lock()
        lock.acquire()
        try:
             self.db.cursor.execute(st, {"session_token": session_token} )
             self.db.connection.commit()
        except:
             lock.release()
             raise SQLException(traceback=traceback.format_exc())
        lock.release()


    def __update_session(self, session_token):
        """
        Refresh the session_token in the db on succesful refresh
        """
        st = """
        UPDATE sessions
        SET session_timestamp=:session_timestamp
        WHERE session_token=:session_token
        """
        #"
        lock = threading.Lock()
        lock.acquire()

        
        self.logger.debug("update_session session_token: %s" % session_token)
        try:
             self.db.cursor.execute(st, {"session_token": session_token,
                                         "session_timestamp": time.time()} )
             self.db.connection.commit()
        except:
             lock.release()
             raise SQLException(traceback=traceback.format_exc())
        lock.release()


    def token_check(self, token):
        """
        Validate that the token passed in to any method call other than user_login
        is correct, and if not, raise an Exception.  Note that all exceptions are
        caught in dispatch, so methods give failing return codes rather than XMLRPCFaults.
        This is a feature, mainly since Rails (and other language bindings) can better
        grok tracebacks this way.
        """

        # for methods calling other methods, they will inadvertently run token check
        # more than once, so they can just pass in None.  None is safe because you can't
        # send it over XMLRPC.
        # FIXME -- is this true, should not be going through dispatch then.

        if token is None:
            return SuccessException()
        
        if not os.path.exists("/var/lib/shadowmanager/primary_db"):
            raise MisconfiguredException(comment="/var/lib/shadowmanager/primary_db doesn't exist")

        self.logger.debug("self.tokens: %s" % self.tokens)
        self.logger.debug("token: %s" % type(token))
        now = time.time()

        st = """
        SELECT session_token, user_id, session_timestamp
        FROM sessions
        WHERE session_token = :session_token"""

        lock = threading.Lock()
        lock.acquire()
        
        try:
            results = self.db.cursor.execute(st, {"session_token": token })
            # no need to fetch all, since session_token is unique
            results = self.db.cursor.fetchone()
        except:
            lock.release()
            raise SQLException(traceback=traceback.format_exc())

        lock.release()

        if results == None:
            raise TokenInvalidException()

        # remove tokens older than 1/2 hour
        if (now - results[2]) > SESSION_LENGTH:
            self.__delete_session(results[0])
            raise TokenExpiredException()
        if results[0] == token:
            # update the expiration counter
            self.__update_session(results[0])
            return SuccessException()
            
        raise TokenInvalidException()
   


    
    
methods = Authentication()

# for this module, we want to do some cleaup on
#startup
methods._cleanup_old_sessions()

register_rpc = methods.register_rpc

