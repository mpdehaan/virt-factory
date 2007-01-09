# the task controller deals with background actions, some of which the user might be interested
# in watching from the UI.  It should show state but allow only a minimum of editing (possibly
# pausing a task) and that's it.
#
# the backend actually uses "action" for the word "task", but the word ActionController is 
# apparently reserved by Rails.

class TaskController < AbstractObjectController

   def object_class
       Task
   end

end
~           
