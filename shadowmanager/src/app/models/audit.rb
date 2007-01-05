# the audit model isn't being used right now.  The idea was it would be used for storing
# actions a user takes (like stopping a foo) in the DB.  It definitely will not be using
# ActiveRecord in the "real" version but would be doing WS stuff.

class Audit < ActiveRecord::Base
end
