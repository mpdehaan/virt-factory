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
    
    machine_tags_column = Column('tags',String(4000),nullable=True)
    deployment_tags_column = Column('tags',String(4000),nullable=True)

    return { 
        machine_tags_column:     machines_table,
        deployment_tags_column:  deployments_table
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
    
