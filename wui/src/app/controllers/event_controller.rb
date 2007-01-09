
# Events are going to be used for loggable activity, such as user started/stopped this, or provisioned that.
# Events are likely going to be a Round2 feature.
#---
# TODO: implement event support in WUI/backend in the future.
#+++

class EventController < ApplicationController
   scaffold :event
  
   def index
   end

end
