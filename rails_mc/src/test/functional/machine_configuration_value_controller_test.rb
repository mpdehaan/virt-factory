require File.dirname(__FILE__) + '/../test_helper'
require 'machine_configuration_value_controller'

# Re-raise errors caught by the controller.
class MachineConfigurationValueController; def rescue_action(e) raise e end; end

class MachineConfigurationValueControllerTest < Test::Unit::TestCase
  def setup
    @controller = MachineConfigurationValueController.new
    @request    = ActionController::TestRequest.new
    @response   = ActionController::TestResponse.new
  end

  # Replace this with your real tests.
  def test_truth
    assert true
  end
end
