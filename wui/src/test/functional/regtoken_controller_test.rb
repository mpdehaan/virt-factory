require File.dirname(__FILE__) + '/../test_helper'
require 'regtoken_controller'

# Re-raise errors caught by the controller.
class RegtokenController; def rescue_action(e) raise e end; end

class RegtokenControllerTest < Test::Unit::TestCase
  def setup
    @controller = RegtokenController.new
    @request    = ActionController::TestRequest.new
    @response   = ActionController::TestResponse.new
  end

  # Replace this with your real tests.
  def test_truth
    assert true
  end
end
