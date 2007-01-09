# the user controller handles management and display of users.
# right now, all we do is create entries in the database that can be used for login id/password.
# this may eventually expanded to include different levels of access rights.

# TODO: one thing we'll eventually want to do (probably) is see what actions a given user has taken in
# the logfiles, or if not using logfiles for storage, log entries in the DB.  That's future stuff
# though.


class UserController < AbstractObjectController

   def object_class
       User
   end

end
