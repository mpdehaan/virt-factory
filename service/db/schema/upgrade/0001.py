from sqlalchemy import *
from migrate import *
from migrate.changeset import *

from datetime import datetime

meta = BoundMetaData(migrate_engine)
tables = []

tables.append(Table('users', meta,
    Column('id', Integer, Sequence('userid'), primary_key=True),
    Column('username', String(255), nullable=False, unique=True),
    Column('password', String(255), nullable=False),
    Column('first', String(255)),
    Column('middle', String(255)),
    Column('last', String(255)),
    Column('description', String(255)),
    Column('email', String(255)),
    useexisting=True,
))
      
tables.append(Table('distributions', meta,
    Column('id', Integer, Sequence('distid'), primary_key=True),
    Column('kernel', String(255)),
    Column('initrd', String(255)),
    Column('options', String(255)),
    Column('kickstart', String(255)),
    Column('name', String(255), unique=True),
    Column('architecture', Integer),
    Column('kernel_options', String(255)),
    Column('kickstart_metadata', String(255)),
    useexisting=True,
))

tables.append(Table('profiles', meta,
    Column('id', Integer, Sequence('profileid'), primary_key=True),
    Column('name', String(255), unique=True),
    Column('version', String(255)),
    Column('distribution_id',
        Integer, 
        ForeignKey('distributions.id', ondelete="cascade"), 
        nullable=False),
    Column('virt_storage_size', Integer),
    Column('virt_ram', Integer),
    Column('kickstart_metadata', String(255)),
    Column('kernel_options', String(255)),
    Column('valid_targets', Integer),
    Column('is_container', Integer),
    Column('puppet_classes', TEXT),
    useexisting=True,
))

tables.append(Table('machines', meta,
    Column('id', Integer, Sequence('machineid'), primary_key=True),
    Column('hostname', String(255)),
    Column('ip_address', String(255)),
    Column('registration_token', String(255)),
    Column('architecture', Integer),
    Column('processor_speed', Integer),
    Column('processor_count', Integer),
    Column('memory', Integer),
    Column('kernel_options', String(255)),
    Column('kickstart_metadata', String(255)),
    Column('list_group', String(255)),
    Column('mac_address', String(255)),
    Column('is_container', Integer),
    Column('profile_id',
        Integer,
        ForeignKey('profiles.id', ondelete="cascade"), 
        nullable=False),
    Column('puppet_node_diff', TEXT),
    Column('netboot_enabled', Integer),
    Column('is_locked', Integer),
    useexisting=True,
))
 
tables.append(Table('deployments', meta,
    Column('id', Integer, Sequence('deploymentid'), primary_key=True),
    Column('hostname', String(255)),
    Column('ip_address', String(255)),
    Column('registration_token', String(255)),
    Column('mac_address', String(255)),
    Column('machine_id',
        Integer, 
        ForeignKey('machines.id', ondelete="cascade"),
        nullable=False),
    Column('profile_id',
        Integer,
        ForeignKey('profiles.id', ondelete="cascade"),
        nullable=False),
    Column('state', Integer),
    Column('display_name', String(255)),
    Column('puppet_node_diff', TEXT),
    Column('netboot_enabled', Integer),
    Column('is_locked', Integer),
    useexisting=True,
))

tables.append(Table('regtokens', meta,
    Column('id', Integer, Sequence('regtokenid'), primary_key=True),
    Column('token', String(255)),
    Column('profile_id', Integer, ForeignKey('profiles.id')),
    Column('uses_remaining', Integer),
    useexisting=True,
))

tables.append(Table('sessions', meta,
    Column('id', Integer, Sequence('ssnid'), primary_key=True),
    Column('session_token', String(255), nullable=False, unique=True),
    Column('user_id', 
        Integer, 
        ForeignKey('users.id', ondelete="cascade"), 
        nullable=False),
    Column('session_timestamp',
        DateTime, 
        nullable=False,
        default=datetime.utcnow()),
    useexisting=True,
))

tables.append(Table('tasks', meta, 
    Column('id', Integer, Sequence('taskid'), primary_key=True),
    Column('user_id',
        Integer,
        ForeignKey('users.id', ondelete="cascade"), 
        nullable=False),
    Column('action_type', Integer, nullable=False),
    Column('machine_id',
        Integer, 
        ForeignKey('machines.id', ondelete="cascade"), 
        nullable=False),
    Column('deployment_id', 
        Integer, 
        ForeignKey('deployments.id', ondelete="cascade"), 
        nullable=False),
    Column('state', Integer, nullable=False),
    Column('time',
        DateTime, 
        nullable=False,
        default=datetime.utcnow()),
    useexisting=True,
))

tables.append(Table('events', meta,
          Column('id', Integer, Sequence('eventid'), primary_key=True),
          Column('time', Integer, nullable=False),
          Column('user_id',
                 Integer, 
                 ForeignKey('users.id', ondelete="cascade"), 
                 nullable=False),
          Column('machine_id', Integer, ForeignKey('machines.id')),
          Column('deployment_id', Integer, ForeignKey('deployments.id')),
          Column('profile_id', Integer, ForeignKey('profiles.id')),
          Column('severity', Integer, nullable=False),
          Column('category', String(255), nullable=False),
          Column('action', String(255), nullable=False),
          Column('user_comment', String(255)),
    useexisting=True,
))

def upgrade():
    for t in tables:
        t.create(checkfirst=True)
    

def downgrade():
    mylist = list(tables)
    mylist.reverse()
    for t in mylist:
        t.drop(checkfirst=True)
    
