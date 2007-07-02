from sqlalchemy import *
from migrate import *
from migrate.changeset import *

from datetime import datetime

meta = BoundMetaData(migrate_engine)
tables = []  # no new tables

# provides a static dictionary of tables.
table = dict([(t.name, t) for t in tables])


def column_additions():

    machines_table = sqlalchemy.Table('machines',meta) 
    state_column = Column('state',String(255),nullable=True)
    create_column(state_column,table=machines_table)

    deployments_table = sqlalchemy.Table('deployments',meta) 
    auto_start_column = Column('auto_start',Integer,nullable=True)
    create_column(auto_start_column,table=deployments_table)

def column_removals():
    # FIXME
    pass

def initial_inserts():
    # no inserts for this step
    pass
 
def upgrade():
    for t in tables:
        t.create(checkfirst=True)
    initial_inserts()
    column_additions()

def downgrade():
    mylist = list(tables)
    mylist.reverse()
    for t in mylist:
        t.drop(checkfirst=True)
    
