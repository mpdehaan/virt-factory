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

def column_additions(connection):
    for c, t in columns.items():
        create_column(c, table=t, connection=connection)

def column_removals(connection):
    for c, t in columns.items():
        drop_column(c, table=t, connection=connection)
        

def initial_inserts(connection):
    # no inserts for this step
    pass
 
def upgrade():
    connection = migrate_engine.connect()   # Connection
    session = create_session(bind_to=connection)
    transaction = connection.begin()

    try:
        for t in tables:
            t.create(connectable=connection, checkfirst=True)
        initial_inserts(connection)
        column_additions(connection)
        session.flush()
    except:
        transaction.rollback()
        raise
    transaction.commit()

def downgrade():
    connection = migrate_engine.connect()   # Connection
    session = create_session(bind_to=connection)
    transaction = connection.begin()

    try:
        column_removals(connection)
        mylist = list(tables)
        mylist.reverse()
        for t in mylist:
            t.drop(connectable=connection, checkfirst=True)
        session.flush()
    except:
        transaction.rollback()
        raise
    transaction.commit()
    
