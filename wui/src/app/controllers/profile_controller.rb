
# Profiles are either virtual or bare metal appliance profiles that can be provisioned to machines (dom0 containers and 
# bare metal appliances) or deployed with a Deployment entry (domU's).
 
class ProfileController < AbstractObjectController

   def edit
       # the profile edit box needs to allow picking, via drop down, all of the values for possible distributions.
       #---
       # NOTE: in the future, it may be that certain profiles are incompatible with certain distributions, but let's
       # fight that when we come to it.
       #+++
       super
       @distributions = ManagedObject.retrieve_all(Distribution, get_login).collect do |dist|
           [dist.name, dist.id]
       end
       # the list needs to start off with no selection in the GUI.
       @distributions.insert(0,EMPTY_ENTRY)
   end

   def object_class
       Profile
   end

end

