# the registration token controller is responsible for creating, listing, and removing registration
# tokens that are used to enslave, I mean, register systems to shadowmanager.

class RegtokenController < AbstractObjectController

   def object_class
       Regtoken
   end

   def edit
       super

       @images = []
       ManagedObject.retrieve_all(Image, @session).each do |image|
           @images << [image.name, image.id]
       end
       @images.insert(0,EMPTY_ENTRY)
   end

end

