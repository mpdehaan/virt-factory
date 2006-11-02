class CreateMetrics < ActiveRecord::Migration
  def self.up
    create_table :metrics do |t|
      # t.column :name, :string
    end
  end

  def self.down
    drop_table :metrics
  end
end
