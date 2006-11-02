require File.dirname(__FILE__) + '/../test_helper'
require 'deployment_field_types_controller'

# Re-raise errors caught by the controller.
class DeploymentFieldTypesController; def rescue_action(e) raise e end; end

class DeploymentFieldTypesControllerTest < Test::Unit::TestCase
  def setup
    @controller = DeploymentFieldTypesController.new
    @request    = ActionController::TestRequest.new
    @response   = ActionController::TestResponse.new
  end

  # Replace this with your real tests.
  def test_truth
    assert true
  end
end
