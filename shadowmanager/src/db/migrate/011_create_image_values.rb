class CreateImageValues < ActiveRecord::Migration
  def self.up
    create_table :image_values do |t|
      # t.column :name, :string
    end
  end

  def self.down
    drop_table :image_values
  end
end
