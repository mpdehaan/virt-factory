#!/usr/bin/python


## Virt-factory backend code.
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


from server.codes import *
from server import db
import web_svc

from datetime import datetime

import base64
import threading
import time

SESSION_LENGTH=30*60

class Authentication(web_svc.WebSvc):
    tokens = []
    def __init__(self):
        self.methods = {"user_login": self.user_login,
                        "token_check": self.token_check}
        web_svc.WebSvc.__init__(self)
        self.__lock = threading.Lock()


    def user_login(self, username, password):
         """
         Try to log in user with (user,password) and return a token, or raise
         UserInvalidException or PasswordInvalidException on error.
         """
         # this method is the exception to the rule and doesn't do object validation.
         # login is the only special method like this in the whole API.  It's also
         # the only method that doesn't take a hash for a parameter, though this
         # should probably change for consistancy.    
         # the system account cannot be used to obtain a token under any circumstances. 
         # it exists for database referential integrity when logging, or when creating tasks (etc).
         if username == "system":
             raise UserInvalidException(comment=username)

         user = None
         token = self.next_token()
         session = db.open_session()
         try:
             query = session.query(db.User)
             user = query.selectfirst_by(username=username)
         finally:
             session.close()
             
         if user is None:
             raise UserInvalidException(comment=username)
         if password != user.password:
             raise PasswordInvalidException(comment=username)
          
         ssn = db.Session()
         ssn.user_id = user.id
         ssn.session_token = token
         user.sessions.append(ssn)
         session.save(ssn)
         session.flush()
         
         self.cleanup_old_sessions()
         
         return success(data=token)


    def init_resources(self):
        """
        Initialize resources which includes deleting expired sessions and
        making sure that the admin user exists.
        """
        session = db.open_session()
        try:
            self.cleanup_old_sessions()
            # make sure the 'admin' user exists.
            for user in session.query(db.User).select_by(username='admin'):
                return
            user = db.User()
            user.username = 'admin'
            user.password = 'admin'
            user.first = 'System'
            user.last = 'Administrator'
            user.description = 'The system administrator'
            user.email = 'admin@yourdomain.com'
            session.save(user)
            session.flush()
        finally:
            session.close()
            
    def cleanup_old_sessions(self):
        """
        Delete expired sessions.
        """
        session = db.open_session()
        self.__lock.acquire()
        try:
            # cleanup expired sessions.
            mark = self.expired_mark()
            query = session.query(db.Session)
            for expired in query.select(db.Session.c.session_timestamp < mark):
                session.delete(expired)
            session.flush()
        finally:
            self.__lock.release()
            session.close()


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

        self.logger.debug("token: %s" % type(token))

        valid = False
        session = db.open_session()
        self.__lock.acquire()
        try:
            ssn = session.query(db.Session).selectfirst_by(session_token=token)
            if ssn is not None:
                if ssn.session_timestamp < self.expired_mark():
                    session.delete(ssn)
                else:
                    valid = True
                    ssn.session_timestamp = datetime.utcnow()
                    session.save(ssn)
                session.flush()
        finally:
            self.__lock.release()
            session.close()

        if not valid:
            raise TokenInvalidException()
        
        return SuccessException()
    
    def expired_mark(self):
        hack = (time.time()-SESSION_LENGTH)
        return datetime.utcfromtimestamp(hack)
    
    def next_token(self):
         urandom = open("/dev/urandom")
         token = base64.b64encode(urandom.read(100)) 
         urandom.close()
         return token


    
methods = Authentication()
register_rpc = methods.register_rpc


