require File.dirname(__FILE__) + '/../test_helper'
require 'image_field_types_controller'

# Re-raise errors caught by the controller.
class ImageFieldTypesController; def rescue_action(e) raise e end; end

class ImageFieldTypesControllerTest < Test::Unit::TestCase
  def setup
    @controller = ImageFieldTypesController.new
    @request    = ActionController::TestRequest.new
    @response   = ActionController::TestResponse.new
  end

  # Replace this with your real tests.
  def test_truth
    assert true
  end
end
