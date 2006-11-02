require File.dirname(__FILE__) + '/../test_helper'
require 'deployment_configuration_value_controller'

# Re-raise errors caught by the controller.
class DeploymentConfigurationValueController; def rescue_action(e) raise e end; end

class DeploymentConfigurationValueControllerTest < Test::Unit::TestCase
  def setup
    @controller = DeploymentConfigurationValueController.new
    @request    = ActionController::TestRequest.new
    @response   = ActionController::TestResponse.new
  end

  # Replace this with your real tests.
  def test_truth
    assert true
  end
end
