## Copyright 2006, Red Hat, Inc
##
## This software may be freely redistributed under the terms of the GNU
## general public license.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#
# Notes:
##################################################
# - The tables are created with foreign key constraints and indexes.
#    FK constraints are set for cascading delete when the FK is not-null.
# - The ORM mappers are setup with bidirectional relationships to mirror
#    the constraints.  This ensures that the model maintained by the session matches
#    the current state in the database.
# - Tables are not auto-loaded because the constraint information is lost.
# - All sqlalchemy objects are created in static lists to ensure they exist and
#    are only created once.
# - The global metadata and engine are configured and used.  This can be
#    changed in the event that we need more then one context.
# - The session is wrappered in a dispatcher object.  The purpose of this is to wrapper
#    the sqlalchemy exceptions in SQLException.  Since the session is the primary source
#    of exceptions and the most heavily used, having it raise SQLException allows users
#    to (easily) use a try: finally: block.  Since python <2.5 does not support try:catch:finally,
#    this should help keep the code clean.
#
# TODO: This module needs to be broken up into several modules and
#             placed in its own package.

import traceback
import threading
from sqlalchemy import *
from datetime import datetime
from codes import SQLException

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

#
# provides a static dictionary of tables.
#
table = dict([(t.name, t) for t in tables])


indexes =\
(
    #Index('username', table['users'].c.username, unique=True),
)


class Base(object):
    def fields(self):
        return ormbindings.get(self.__class__, ())
    def data(self, filter=[]):
        result = {}
        for key in self.fields():
            if key in filter:
                continue
            value = getattr(self, key)
            if value is not None:
                result[key] = value
        return result


class User(Base):
    pass
class Distribution(Base):
    pass
class Profile(Base):
    pass
class Machine(Base):
    pass
class Deployment(Base):
    pass
class RegToken(Base):
    pass
class Session(Base):
    pass
class SchemaVersion(Base):
    pass
class Task(Base):
    pass
class Event(Base):
    pass
class UpgradeLogMessage(Base):
    pass


mappers =\
(
    mapper(User, table['users'],
        properties={
            'sessions' : relation(Session, cascade="delete-orphan", lazy=True),
            'tasks' : relation(Task, cascade="delete-orphan", lazy=True),
            'events' : relation(Task, cascade="delete-orphan", lazy=True),
            }),
    mapper(Distribution, table['distributions']),
    mapper(Profile, table['profiles'],
        properties={
            'distribution' : relation(Distribution, lazy=True),
            'machines' : relation(Machine, cascade="delete-orphan", lazy=True),
            'deployments' : relation(Deployment, cascade="delete-orphan", lazy=True),
            'regtokens' : relation(RegToken, lazy=True)
            }),
    mapper(Machine, table['machines'],
        properties={
            'profile' : relation(Profile, lazy=True),
            'tasks' : relation(Task, cascade="delete-orphan", lazy=True),
            'events' : relation(Event, lazy=True),
            }),
    mapper(Deployment, table['deployments'],
        properties={
            'profile' : relation(Profile, lazy=True),
            'machine' : relation(Machine, lazy=True),
            'tasks' : relation(Task, cascade="delete-orphan", lazy=True),
            'events' : relation(Event, lazy=True),
            }),
    mapper(RegToken, table['regtokens'],
        properties={
            'profile' : relation(Profile, lazy=True),
            }),
    mapper(Session, table['sessions'],
        properties={
            'user' : relation(User, lazy=True),
            }),
    mapper(SchemaVersion, table['schema_versions']),
    mapper(Task, table['tasks'],
        properties={
            'user' : relation(User, lazy=True),
            'machine' : relation(Machine, lazy=True),
            'deployment' : relation(Deployment, lazy=True),
            }),
    mapper(Event, table['events'],
        properties={
            'user' : relation(User, lazy=True),
            'machine' : relation(Machine, lazy=True),
            'deployment' : relation(Deployment, lazy=True),
            }),
    mapper(UpgradeLogMessage, table['upgrade_log_messages']),
)


#
# provides a static dictionary of orm classes to mapped
# table column names.
#
ormbindings =\
    dict([(m.class_,[c.name for c in m.local_table.columns]) for m in mappers ])


class Database:
    """
    Represents the database and provides database lifecycle and
    other convienience methods.
    """
    primary = None
    
    def __init__(self, url=None):
        """
        Constructor, sets itself as the primary database.
        It currently uses the global engine and metadata.  We can change this
        if we need to have more then one primary database.
        @param url: a sqlalchemy database url.
        @type url: string 
        """
        Database.primary = self
        global_connect(url, echo=True)
        
    def create(self):
        """
        Create all tables, indexes and constraints that have not
        yet been created.
        """
        # TODO: create the database here?
        for t in tables:
            t.create(checkfirst=True)
    
    def drop(self):
        """
        Drop all tables, indexes and constraints.
        """
        mylist = list(tables)
        mylist.reverse()
        for t in mylist:
            t.drop(checkfirst=True)
        
    def open_session(self):
        """
        A convienience method used to create a session.
        The primary purposes are to wrapper the exception and
        limit the need for sqlalchemy imports throughout the code.
        @return: A session wrapped in a L{Facade} that mainly
            wrappers the sqlalchemy exceptions.
        @rtype: L{Facade}
        """
        try:
            return Facade(create_session())
        except:
            raise SQLException(traceback=traceback.format_exc())


class Facade:
    def __init__(self, session):
        self.session = session
        
    def __getattr__(self, name):
        attribute = getattr(self.session, name)
        if callable(attribute):
            return Facade.Method(attribute)
        else:
            return attribute
    
    class Method:
        def __init__(self, method):
            self.method = method
        
        def __call__(self, *args):
            try:
                return self.method(*args)
            except Exception, e:
                raise SQLException(
                           comment = str(e),
                           traceback=traceback.format_exc())


def open_session():
    """
    Convienience method provided simply code.  Most code using this
    module can simply (import db) and create a session as: db.open_session()
    and not deal with the Database object.
    """
    if Database.primary is None:
        raise SQLException(comment='Primary database not initialized')
    return Database.primary.open_session()



if __name__ == '__main__':
    database = Database('postgres://jortel:jortel@localhost/virtfactory')
    #database.drop()
    #database.create()
        
    ssn = open_session()
    try:
        user = User()
        user.username = 'jortel'
        user.password = 'mypassword'
        user.first = 'Elvis'
        user.last = 'Prestley'
        user.description = 'The King.'
        user.email = 'elvis@redhat.com'
        ssn.save(user)
        
        session = Session()
        session.session_token = 'my token'
        user.sessions.append(session)

        ssn.save(session)
        ssn.flush()
        
        for user in ssn.query(User).select(limit=10, offset=0):
            print user.last

        ssn.delete(user)
        ssn.flush()
    finally:
        ssn.close()
        
