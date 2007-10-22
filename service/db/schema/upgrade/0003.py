from sqlalchemy import *
from migrate import *
from migrate.changeset import *

from datetime import datetime

meta = BoundMetaData(migrate_engine)
tables = []

Database.tables.append(Table('tags', Database.meta,
    Column('id', Integer, Sequence('tagid'), primary_key=True),
    Column('name', String(255), unique=True)
))
        
Database.tables.append(Table('machine_tags', Database.meta,
    Column('tag_id', Integer, ForeignKey('tags.id')),
    Column('machine_id', Integer, ForeignKey('machines.id'))
))
        
Database.tables.append(Table('deployment_tags', Database.meta,
    Column('tag_id', Integer, ForeignKey('tags.id')),
    Column('deployment_id', Integer, ForeignKey('deployments.id'))
))

# provides a static dictionary of tables.
table = dict([(t.name, t) for t in tables])


def get_columns():
    return {}

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
    
