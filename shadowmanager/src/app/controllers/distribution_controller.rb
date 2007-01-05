
# The distribution controller allows editing and viewing distributions.  It has no fancy functionality as the
# distribution is the most basic of classes.  There are pretty much view only.  A user imports distributions into
# cobbler using the "shadow import" command prior to using the WebUI.
#---
# FIXME:  we don't display these in the UI except in drop downs.  Do we want to?
#+++

class DistributionController < AbstractObjectController

   def object_class
       Distribution
   end

end
