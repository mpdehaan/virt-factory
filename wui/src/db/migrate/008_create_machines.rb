class CreateMachines < ActiveRecord::Migration
  def self.up
    create_table :machines do |t|
      # t.column :name, :string
    end
  end

  def self.down
    drop_table :machines
  end
end
