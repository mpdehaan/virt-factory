# FIXME: we're not using this at all right now and this probably can be deleted.
# however, in round 2, it may surface again.  We probably want a model class that
# deals with something like RRD, rather than something database centric.

class MetricController < ApplicationController
    scaffold :metric
end
