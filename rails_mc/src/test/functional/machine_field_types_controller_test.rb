require File.dirname(__FILE__) + '/../test_helper'
require 'machine_field_types_controller'

# Re-raise errors caught by the controller.
class MachineFieldTypesController; def rescue_action(e) raise e end; end

class MachineFieldTypesControllerTest < Test::Unit::TestCase
  def setup
    @controller = MachineFieldTypesController.new
    @request    = ActionController::TestRequest.new
    @response   = ActionController::TestResponse.new
  end

  # Replace this with your real tests.
  def test_truth
    assert true
  end
end
