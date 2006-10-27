class CreateMachineValues < ActiveRecord::Migration
  def self.up
    create_table :machine_values do |t|
      # t.column :name, :string
    end
  end

  def self.down
    drop_table :machine_values
  end
end
