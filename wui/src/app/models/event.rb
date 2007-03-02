# we're not using events yet.  They won't use active record when we are using them.
# events are more machine generated than audit, or does audit go away entirely?

class Event < ActiveRecord::Base
end
