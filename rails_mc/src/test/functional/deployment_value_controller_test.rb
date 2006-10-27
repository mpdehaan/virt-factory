require File.dirname(__FILE__) + '/../test_helper'
require 'deployment_value_controller'

# Re-raise errors caught by the controller.
class DeploymentValueController; def rescue_action(e) raise e end; end

class DeploymentValueControllerTest < Test::Unit::TestCase
  def setup
    @controller = DeploymentValueController.new
    @request    = ActionController::TestRequest.new
    @response   = ActionController::TestResponse.new
  end

  # Replace this with your real tests.
  def test_truth
    assert true
  end
end
