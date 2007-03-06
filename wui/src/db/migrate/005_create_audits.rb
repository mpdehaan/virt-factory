class CreateAudits < ActiveRecord::Migration
  def self.up
    create_table :audits do |t|
      # t.column :name, :string
    end
  end

  def self.down
    drop_table :audits
  end
end
