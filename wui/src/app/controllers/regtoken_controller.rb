# the registration token controller is responsible for creating, listing, and removing registration
# tokens that are used to enslave, I mean, register systems to virt-factory.

class RegtokenController < AbstractObjectController

   def object_class
       Regtoken
   end

   def edit
       super

       @profiles = []
       ManagedObject.retrieve_all(Profile, @session).each do |profile|
           @profiles << [profile.name, profile.id]
       end
       @profiles.insert(0,EMPTY_ENTRY)
   end

end

