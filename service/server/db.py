from sqlalchemy import *
from datetime import datetime
from property import Property

tables =\
(
    Table('users',
          Column('id', Integer, Sequence('userid'), primary_key=True),
          Column('username', String(255), nullable=False, unique=True),
          Column('password', String(255), nullable=False),
          Column('first', String(255), nullable=False),
          Column('middle', String(255)),
          Column('last', String(255), nullable=False),
          Column('description', String(255)),
          Column('email', String(255), nullable=False)),
      Table('distributions',
          Column('id', Integer, Sequence('distid'), primary_key=True),
          Column('kernel', String(255), nullable=False),
          Column('initrd', String(255), nullable=False),
          Column('options', String(255)),
          Column('kickstart', String(255)),
          Column('name', String(255), unique=True),
          Column('architecture', Integer, nullable=False),
          Column('kernel_options', String(255)),
          Column('kickstart_metadata', String(255))),
    Table('profiles',
        Column('id', Integer, Sequence('profileid'), primary_key=True),
        Column('name', String(255), unique=True),
        Column('version', String(255), nullable=False),
        Column('distribution_id',
               Integer, 
               ForeignKey('distributions.id', ondelete="cascade"), 
               nullable=False),
        Column('virt_storage_size', Integer),
        Column('virt_ram', Integer),
        Column('kickstart_metadata', String(255)),
        Column('kernel_options', String(255)),
        Column('valid_targets', Integer, nullable=False),
        Column('is_container', Integer, nullable=False),
        Column('puppet_classes', TEXT)),
    Table('machines',
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
        Column('is_locked', Integer)),
    Table('deployments',
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
        Column('state', Integer, nullable=False),
        Column('display_name', String(255), nullable=False),
        Column('puppet_node_diff', TEXT),
        Column('netboot_enabled', Integer),
        Column('is_locked', Integer)),
    Table('regtokens',
        Column('id', Integer, Sequence('regtokenid'), primary_key=True),
        Column('token', String(255)),
        Column('profile_id', Integer, ForeignKey('profiles.id')),
        Column('uses_remaining', Integer)),
    Table('sessions',
        Column('id', Integer, Sequence('ssnid'), primary_key=True),
        Column('session_token', String(255), nullable=False, unique=True),
        Column('user_id', 
               Integer, 
               ForeignKey('users.id', ondelete="cascade"), 
               nullable=False),
        Column('session_timestamp',
               DateTime, 
               nullable=False,
               default=datetime.utcnow())),
    Table('schema_versions',
        Column('id', Integer, Sequence('schemaverid'), primary_key=True),
        Column('version', Integer),
        Column('git_tag', String(100)),
        Column('install_timestamp',
               DateTime, 
               nullable=False,
               default=datetime.utcnow()),
        Column('status', String(20),  nullable=False),
        Column('notes', String(4000))),
    Table('tasks', 
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
                 default=datetime.utcnow())),
    Table('events',
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
          Column('user_comment', String(255))),
    Table('upgrade_log_messages',
        Column('id', Integer, Sequence('uglogmsgid'), primary_key=True),
        Column('action', String(50)),
        Column('message_type', String(50)),
        Column('message_timestamp',
               DateTime,
               default=datetime.utcnow()),
        Column('message', String(4000)))
)

table = Property(dict([(t.name, t) for t in tables]), True)

indexes =\
(
    #Index('username', table.users.c.username, unique=True),
)


class User(object):
    pass
class Distribution(object):
    pass
class Profile(object):
    pass
class Machine(object):
    pass
class Deployment(object):
    pass
class RegToken(object):
    pass
class Session(object):
    pass
class SchemaVersion(object):
    pass
class Task(object):
    pass
class Event(object):
    pass
class UpgradeLogMessage(object):
    pass


mappers =\
(
    mapper(User, table.users,
        properties={
            'sessions' : relation(Session, cascade="delete-orphan", lazy=True),
            'tasks' : relation(Task, cascade="delete-orphan", lazy=True),
            'events' : relation(Task, cascade="delete-orphan", lazy=True),
            }),
    mapper(Distribution, table.distributions),
    mapper(Profile, table.profiles,
        properties={
            'distribution' : relation(Distribution, lazy=True),
            'machines' : relation(Machine, cascade="delete-orphan", lazy=True),
            'deployments' : relation(Deployment, cascade="delete-orphan", lazy=True),
            'regtokens' : relation(RegToken, lazy=True)
            }),
    mapper(Machine, table.machines,
        properties={
            'profile' : relation(Profile, lazy=True),
            'tasks' : relation(Task, cascade="delete-orphan", lazy=True),
            'events' : relation(Event, lazy=True),
            }),
    mapper(Deployment, table.deployments,
        properties={
            'profile' : relation(Profile, lazy=True),
            'machine' : relation(Machine, lazy=True),
            'tasks' : relation(Task, cascade="delete-orphan", lazy=True),
            'events' : relation(Event, lazy=True),
            }),
    mapper(RegToken, table.regtokens,
        properties={
            'profile' : relation(Profile, lazy=True),
            }),
    mapper(Session, table.sessions,
        properties={
            'user' : relation(User, lazy=True),
            }),
    mapper(SchemaVersion, table.schema_versions),
    mapper(Task, table.tasks,
        properties={
            'user' : relation(User, lazy=True),
            'machine' : relation(Machine, lazy=True),
            'deployment' : relation(Deployment, lazy=True),
            }),
    mapper(Event, table.events,
        properties={
            'user' : relation(User, lazy=True),
            'machine' : relation(Machine, lazy=True),
            'deployment' : relation(Deployment, lazy=True),
            }),
    mapper(UpgradeLogMessage, table.upgrade_log_messages),
)


def connect(url='postgres://jortel:jortel@localhost/virtfactory'):
    global_connect(url, echo=True)
    
def open_session():
    return create_session()
    
def create():
    for t in tables:
        t.create(checkfirst=True)

def drop():
    mylist = list(tables)
    mylist.reverse()
    for t in mylist:
        t.drop(checkfirst=True)


if __name__ == '__main__':
    connect()
    drop()
    create()
        
    ssn = open_session()
    try:
        user = User()
        user.username = 'jortel'
        user.password = 'mypassword'
        user.first = 'jeff'
        user.middle = 'roy'
        user.last = 'ortel'
        user.description = 'test user'
        user.email = 'jortel@redhat.com'
        ssn.save(user)
        
        session = Session()
        session.session_token = 'my token'
        session.uses_remaining = 1
        user.sessions.append(session)

        ssn.save(session)
        ssn.flush()
        
        ssn.delete(user)
        ssn.flush()
    finally:
        ssn.close()

