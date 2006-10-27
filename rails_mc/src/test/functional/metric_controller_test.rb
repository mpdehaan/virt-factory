require File.dirname(__FILE__) + '/../test_helper'
require 'metric_controller'

# Re-raise errors caught by the controller.
class MetricController; def rescue_action(e) raise e end; end

class MetricControllerTest < Test::Unit::TestCase
  def setup
    @controller = MetricController.new
    @request    = ActionController::TestRequest.new
    @response   = ActionController::TestResponse.new
  end

  # Replace this with your real tests.
  def test_truth
    assert true
  end
end
