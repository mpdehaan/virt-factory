class CreateDeploymentConfigurationValues < ActiveRecord::Migration
  def self.up
    create_table :deployment_configuration_values do |t|
      # t.column :name, :string
    end
  end

  def self.down
    drop_table :deployment_configuration_values
  end
end
