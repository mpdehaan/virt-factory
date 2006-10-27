require File.dirname(__FILE__) + '/../test_helper'
require 'permission_controller'

# Re-raise errors caught by the controller.
class PermissionController; def rescue_action(e) raise e end; end

class PermissionControllerTest < Test::Unit::TestCase
  def setup
    @controller = PermissionController.new
    @request    = ActionController::TestRequest.new
    @response   = ActionController::TestResponse.new
  end

  # Replace this with your real tests.
  def test_truth
    assert true
  end
end
