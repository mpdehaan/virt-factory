from sqlalchemy import *
from migrate import *
from migrate.changeset import *

from datetime import datetime

meta = BoundMetaData(migrate_engine)
tables = []  # no new tables

# provides a static dictionary of tables.
table = dict([(t.name, t) for t in tables])


def get_columns():

    machines_table = sqlalchemy.Table('machines',meta) 
    deployments_table = sqlalchemy.Table('deployments',meta) 
    
    state_column = Column('state',String(255),nullable=True)
    hb_column    = Column('last_heartbeat',Integer,nullable=True)
    auto_start_column = Column('auto_start',Integer,nullable=True)
    hb_column2   = Column('last_heartbeat',Integer,nullable=True)

    return { 
        state_column:      machines_table,
        auto_start_column: deployments_table,
        hb_column:         machines_table,
        hb_column2:        deployments_table
    }

columns = get_columns()

def column_additions():

    for c, t in columns.items():
        create_column(c, table=t)

def column_removals():
    for c, t in columns.items():
        drop_column(c, table=t)
        

def initial_inserts():
    # no inserts for this step
    pass
 
def upgrade():
    for t in tables:
        t.create(checkfirst=True)
    initial_inserts()
    column_additions()

def downgrade():
    column_removals()
    mylist = list(tables)
    mylist.reverse()
    for t in mylist:
        t.drop(checkfirst=True)
    
