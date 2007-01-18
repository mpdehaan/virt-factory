# the registration token controller is responsible for creating, listing, and removing registration
# tokens that are used to enslave, I mean, register systems to shadowmanager.

class RegtokenController < AbstractObjectController

   def object_class
       RegToken
   end

   def edit
       super
       # @images = ...
   end

end

