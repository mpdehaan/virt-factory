class CreateDeploymentValues < ActiveRecord::Migration
  def self.up
    create_table :deployment_values do |t|
      # t.column :name, :string
    end
  end

  def self.down
    drop_table :deployment_values
  end
end
