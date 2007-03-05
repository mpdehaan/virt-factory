require File.dirname(__FILE__) + '/../test_helper'
require 'machine_controller'

# Re-raise errors caught by the controller.
class MachineController; def rescue_action(e) raise e end; end

class MachineControllerTest < Test::Unit::TestCase
  def setup
    @controller = MachineController.new
    @request    = ActionController::TestRequest.new
    @response   = ActionController::TestResponse.new
  end

  # Replace this with your real tests.
  def test_truth
    assert true
  end
end
