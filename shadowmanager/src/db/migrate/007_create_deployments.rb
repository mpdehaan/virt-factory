class CreateDeployments < ActiveRecord::Migration
  def self.up
    create_table :deployments do |t|
      # t.column :name, :string
    end
  end

  def self.down
    drop_table :deployments
  end
end
