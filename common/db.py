from sqlalchemy import *
from property import Property

class FKey:
    def __init__(self):
        self.user = ForeignKey('users.id', ondelete="cascade")
        self.profile = ForeignKey('profiles.id', ondelete="cascade")
        self.distribution = ForeignKey('distributions.id', ondelete="cascade")
        self.deployment = ForeignKey('deployments.id', ondelete="cascade")
        self.machine = ForeignKey('machines.id', ondelete="cascade")

tables =\
(
    Table('users',
          Column('id', Integer, Sequence('userid'), primary_key=True),
          Column('username', String(255), nullable=False),
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
        Column('distribution_id', Integer, FKey().distribution, nullable=False),
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
        Column('profile_id', Integer, FKey().profile, nullable=False),
        Column('puppet_node_diff', TEXT),
        Column('netboot_enabled', Integer),
        Column('is_locked', Integer)),
    Table('deployments',
        Column('id', Integer, Sequence('deploymentid'), primary_key=True),
        Column('hostname', String(255)),
        Column('ip_address', String(255)),
        Column('registration_token', String(255)),
        Column('mac_address', String(255)),
        Column('machine_id', Integer, nullable=False),
        Column('profile_id', Integer, FKey().profile, nullable=False),
        Column('state', Integer, nullable=False),
        Column('display_name', String(255), nullable=False),
        Column('puppet_node_diff', TEXT),
        Column('netboot_enabled', Integer),
        Column('is_locked', Integer)),
    Table('regtokens',
        Column('id', Integer, Sequence('regtokenid'), primary_key=True),
        Column('token', String(255)),
        Column('profile_id', Integer, FKey().profile),
        Column('uses_remaining', Integer)),
    Table('sessions',
        Column('id', Integer, Sequence('ssnid'), primary_key=True),
        Column('session_token', String(255), nullable=False, unique=True),
        Column('user_id', Integer, FKey().user, nullable=False),
        Column('session_timestamp', DateTime, nullable=False)),
    Table('schema_versions',
        Column('id', Integer, Sequence('schemaverid'), primary_key=True),
        Column('version', Integer),
        Column('git_tag', String(100)),
        Column('install_timestamp', DateTime, nullable=False),
        Column('status', String(20),  nullable=False),
        Column('notes', String(4000))),
    Table('tasks', 
          Column('id', Integer, Sequence('taskid'), primary_key=True),
          Column('user_id', Integer, FKey().user, nullable=False),
          Column('action_type', Integer, nullable=False),
          Column('machine_id', Integer, FKey().machine, nullable=False),
          Column('deployment_id', Integer, FKey().deployment, nullable=False),
          Column('state', Integer, nullable=False),
          Column('time', DateTime, nullable=False)),
    Table('events',
          Column('id', Integer, Sequence('eventid'), primary_key=True),
          Column('time', Integer, nullable=False),
          Column('user_id', Integer, FKey().user, nullable=False),
          Column('machine_id', Integer, FKey().machine),
          Column('deployment_id', Integer, FKey().deployment),
          Column('profile_id', Integer, FKey().profile),
          Column('severity', Integer, nullable=False),
          Column('category', String(255), nullable=False),
          Column('action', String(255), nullable=False),
          Column('user_comment', String(255))),
    Table('upgrade_log_messages',
        Column('id', Integer, Sequence('uglogmsgid'), primary_key=True),
        Column('action', String(50)),
        Column('message_type', String(50)),
        Column('message_timestamp', DateTime),
        Column('message', String(4000)))
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


table = Property(dict([(t.name, t) for t in tables]), True)

mappers =\
(
    mapper(User, table.users),
    mapper(Distribution, table.distributions),
    mapper(Profile, table.profiles,
           properties=
               {'distributions' : relation(Distribution, lazy=True)}),
    mapper(Machine, table.machines,
           properties=
               {'profiles' : relation(Profile, lazy=True)}),
    mapper(Deployment, table.deployments,
           properties=
               {'profiles' : relation(Profile, lazy=True)}),
    mapper(RegToken, table.regtokens,
           properties=
               {'profiles' : relation(Profile, lazy=True)}),
    mapper(Session, table.sessions,
           properties=
               {'users' : relation(User, lazy=True)}),
    mapper(SchemaVersion, table.schema_versions),
    mapper(Task, table.tasks,
           properties=
               {'users' : relation(User, lazy=True),
                'machines' : relation(Machine, lazy=True),
                'deployments' : relation(Deployment, lazy=True)}),
    mapper(Event, table.events,
           properties=
               {'users' : relation(User, lazy=True),
                'machines' : relation(Machine, lazy=True),
                'deployments' : relation(Deployment, lazy=True)}),
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
        ssn.flush()
    finally:
        ssn.close()

