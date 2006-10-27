class CreateFieldTypes < ActiveRecord::Migration
  def self.up
    create_table :field_types do |t|
      # t.column :name, :string
    end
  end

  def self.down
    drop_table :field_types
  end
end
