class CreateMachineFieldTypes < ActiveRecord::Migration
  def self.up
    create_table :machine_field_types do |t|
      # t.column :name, :string
    end
  end

  def self.down
    drop_table :machine_field_types
  end
end
