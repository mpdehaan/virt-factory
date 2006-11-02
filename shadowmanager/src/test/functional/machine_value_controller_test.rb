require File.dirname(__FILE__) + '/../test_helper'
require 'machine_value_controller'

# Re-raise errors caught by the controller.
class MachineValueController; def rescue_action(e) raise e end; end

class MachineValueControllerTest < Test::Unit::TestCase
  def setup
    @controller = MachineValueController.new
    @request    = ActionController::TestRequest.new
    @response   = ActionController::TestResponse.new
  end

  # Replace this with your real tests.
  def test_truth
    assert true
  end
end
