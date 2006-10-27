class CreateDeploymentFieldTypes < ActiveRecord::Migration
  def self.up
    create_table :deployment_field_types do |t|
      # t.column :name, :string
    end
  end

  def self.down
    drop_table :deployment_field_types
  end
end
