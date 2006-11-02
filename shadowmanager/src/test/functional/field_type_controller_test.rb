require File.dirname(__FILE__) + '/../test_helper'
require 'field_type_controller'

# Re-raise errors caught by the controller.
class FieldTypeController; def rescue_action(e) raise e end; end

class FieldTypeControllerTest < Test::Unit::TestCase
  def setup
    @controller = FieldTypeController.new
    @request    = ActionController::TestRequest.new
    @response   = ActionController::TestResponse.new
  end

  # Replace this with your real tests.
  def test_truth
    assert true
  end
end
