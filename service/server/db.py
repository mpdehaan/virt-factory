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
from sqlalchemy.ext.sessioncontext import SessionContext
from datetime import datetime
from codes import SQLException, NoSuchObjectException

class Base(object):
    def fields(self):
        return Database.ormbindings.get(self.__class__, ())
    
    def get_hash(self, filter=[]):
        result = {}
        for key in self.fields():
            if key in filter:
                continue
            value = getattr(self, key)
            if value is not None:
                result[key] = value
        return result
    
    def update(self, args, filter=('id',)):
        for key in self.fields():
            if key in filter: continue
            if key in args:
                setattr(self, key, args[key])
    
    def __delete(self, session, id):
            session.delete(self.get(session, id))
            session.flush()
                        
    def __get(self, session, id):
        result = session.get(self, id)
        if result is None:
            comment = '%s(id=%s) not-found' % (self, id)
            raise NoSuchObjectException(comment=comment)
        return result
    
    def __list(self, session, offset=0, limit=0, where_args=[]):
        result = []        
        query = session.query(self).offset(offset).limit(limit)
        if where_args:
            result = query.filter_by(**where_args).all()
        else:
            result = query.select()
        return result
    
    get = classmethod(__get)
    delete = classmethod(__delete)
    list = classmethod(__list)

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
class Task(Base):
    pass
class Event(Base):
    pass
class Tag(Base):
    pass



def interpolate_url_password(url):
    if url is None:
        raise SQLException(comment="no connection string specified")
    if url.find("%(password)s") != -1:
        pwfile = open("/etc/virt-factory/db/dbaccess")
        read_pw = pwfile.read()
        pwfile.close()
        url = url % { "password" : read_pw }
    return url

class Database:
    """
    Represents the database and provides database lifecycle and
    other convienience methods.
    """

    __shared_state = {}
    has_loaded = False
    # primary = None 
    ctx = None
    meta = None
    tables = None
    table = None
    indexes = None
    mappers = None

 
    def __init__(self, url=None):
        """
        Constructor, sets itself as the primary database.
        It currently uses the global engine and metadata.  We can change this
        if we need to have more then one primary database.
        @param url: a sqlalchemy database url.
        @type url: string 
        """
        
        self.__dict__ = self.__shared_state

        if not Database.has_loaded:
            self.setup_metadata(interpolate_url_password(url))
            # FIXME: this echo causes output for every query to go to stdout
            # Should always be False in version control. May want to
            # parameterize it.
            Database.meta.connect(interpolate_url_password(url), echo=False)
            Database.has_loaded = True       
 

    def setup_metadata(self,url):
        Database.ctx = SessionContext(create_session)
        Database.meta = BoundMetaData(create_engine(url))
        
        Database.tables = []
        
        Database.tables.append(Table('users', Database.meta,
            Column('id', Integer, Sequence('userid'), primary_key=True),
            Column('username', String(255), nullable=False, unique=True),
            Column('password', String(255), nullable=False),
            Column('first', String(255)),
            Column('middle', String(255)),
            Column('last', String(255)),
            Column('description', String(255)),
            Column('email', String(255))
        ))
          
        Database.tables.append(Table('distributions', Database.meta,
            Column('id', Integer, Sequence('distid'), primary_key=True),
            Column('kernel', String(255)),
            Column('initrd', String(255)),
            Column('options', String(255)),
            Column('kickstart', String(255)),
            Column('name', String(255), unique=True),
            Column('architecture', String(255)),
            Column('kernel_options', String(255)),
            Column('kickstart_metadata', String(255))
        ))
    
        Database.tables.append(Table('profiles', Database.meta,
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
            Column('valid_targets', String(255)),
            Column('is_container', Integer),
            Column('puppet_classes', TEXT),
            Column('virt_type', String(255))
        ))
        
        Database.tables.append(Table('machines', Database.meta,
            Column('id', Integer, Sequence('machineid'), primary_key=True),
            Column('hostname', String(255)),
            Column('ip_address', String(255)),
            Column('registration_token', String(255)),
            Column('architecture', String(255)),
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
            Column('state', String(255)),
            Column('last_heartbeat', Integer)
        ))
         
        Database.tables.append(Table('deployments', Database.meta,
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
            Column('state', String(255)),
            Column('display_name', String(255)),
            Column('puppet_node_diff', TEXT),
            Column('netboot_enabled', Integer),
            Column('is_locked', Integer),
            Column('auto_start', Integer),
            Column('last_heartbeat', Integer)
        ))
        
        Database.tables.append(Table('regtokens', Database.meta,
            Column('id', Integer, Sequence('regtokenid'), primary_key=True),
            Column('token', String(255)),
            Column('profile_id', Integer, ForeignKey('profiles.id')),
            Column('uses_remaining', Integer)
        ))
        
        Database.tables.append(Table('sessions', Database.meta,
            Column('id', Integer, Sequence('ssnid'), primary_key=True),
            Column('session_token', String(255), nullable=False, unique=True),
            Column('user_id', 
                Integer, 
                ForeignKey('users.id', ondelete="cascade"), 
                nullable=False),
            Column('session_timestamp',
                DateTime, 
                nullable=False,
                default=datetime.utcnow())
        ))
        
        Database.tables.append(Table('tasks',  Database.meta,
            Column('id', Integer, Sequence('taskid'), primary_key=True),
            Column('user_id',
                Integer,
                ForeignKey('users.id', ondelete="cascade"), 
                nullable=False),
            Column('action_type', String(255), nullable=False),
            Column('machine_id',
                Integer, 
                ForeignKey('machines.id', ondelete="cascade"), 
                nullable=False),
            Column('deployment_id', 
                Integer, 
                ForeignKey('deployments.id', ondelete="cascade"), 
                nullable=False),
            Column('state', String(255), nullable=False),
            Column('time',
                DateTime, 
                nullable=False,
                default=datetime.utcnow())
        ))
        
        Database.tables.append(Table('events', Database.meta,
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
            Column('user_comment', String(255))
        ))
    
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
        
        #
        # provides a static dictionary of tables.
        #
        Database.table = dict([(t.name, t) for t in Database.tables])
    
    
        Database.indexes =\
        (
            #Index('username', Database.table['users'].c.username, unique=True),
        )
    
    
        Database.mappers =\
        (
            mapper(User, Database.table['users'], extension=Database.ctx.mapper_extension,
                properties={
                    'sessions' : relation(Session, passive_deletes=True, viewonly=True, lazy=True),
                    'tasks' : relation(Task, passive_deletes=True, viewonly=True, lazy=True),
                    'events' : relation(Task, passive_deletes=True, viewonly=True, lazy=True),
                    }),
            mapper(Distribution, Database.table['distributions'], extension=Database.ctx.mapper_extension),
            mapper(Profile, Database.table['profiles'], extension=Database.ctx.mapper_extension,
                properties={
                    'distribution' : relation(Distribution, lazy=True),
                    'machines' : relation(Machine, passive_deletes=True, viewonly=True, lazy=True),
                    'deployments' : relation(Deployment, passive_deletes=True, viewonly=True, lazy=True),
                    'regtokens' : relation(RegToken, lazy=True)
                    }),
            mapper(Machine, Database.table['machines'], extension=Database.ctx.mapper_extension,
                properties={
                    'profile' : relation(Profile, lazy=True),
                    'tasks' : relation(Task, passive_deletes=True, viewonly=True, lazy=True),
                    'events' : relation(Event, lazy=True),
                    }),
            mapper(Deployment, Database.table['deployments'], extension=Database.ctx.mapper_extension,
                properties={
                    'profile' : relation(Profile, lazy=True),
                    'machine' : relation(Machine, lazy=True),
                    'tasks' : relation(Task, passive_deletes=True, viewonly=True, lazy=True),
                    'events' : relation(Event, lazy=True),
                    }),
            mapper(RegToken, Database.table['regtokens'], extension=Database.ctx.mapper_extension,
                properties={
                    'profile' : relation(Profile, lazy=True),
                    }),
            mapper(Session, Database.table['sessions'], extension=Database.ctx.mapper_extension,
                properties={
                    'user' : relation(User, lazy=True),
                    }),
            mapper(Task, Database.table['tasks'], extension=Database.ctx.mapper_extension,
                properties={
                    'user' : relation(User, lazy=True),
                    'machine' : relation(Machine, lazy=True),
                    'deployment' : relation(Deployment, lazy=True),
                    }),
            mapper(Event, Database.table['events'], extension=Database.ctx.mapper_extension,
                properties={
                    'user' : relation(User, lazy=True),
                    'machine' : relation(Machine, lazy=True),
                    'deployment' : relation(Deployment, lazy=True),
                    }),
            mapper(Tag, Database.table['tags'], extension=Database.ctx.mapper_extension,
                properties={
                    'machines' : relation(Machine, secondary=Database.table['machine_tags'], backref='tags'),
                    'deployments' : relation(Deployment, secondary=Database.table['deployment_tags'], backref='tags'),
                    }),
        )
    
        #
        # provides a static dictionary of orm classes to mapped
        # table column names.
        #
        Database.ormbindings =\
            dict([(m.class_,[c.name for c in m.local_table.columns]) for m in Database.mappers ])

    def create(self):
        """
        Create all tables, indexes and constraints that have not
        yet been created.
        """
        for t in Database.tables:
            t.create(checkfirst=True)
    
    def drop(self):
        """
        Drop all tables, indexes and constraints.
        """
        mylist = list(Database.tables)
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
            return Facade()
        except:
            print traceback.format_exc()
            raise SQLException(traceback=traceback.format_exc())


class Facade:
    def __init__(self):
        pass

    def __getattr__(self, name):
        attribute = getattr(Database.ctx.current, name)
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
                # FIXME: not sure if loggers work here, until then..
                traceback.print_exc()
                raise SQLException(
                           comment = str(e),
                           traceback=traceback.format_exc())


def open_session():
    """
    Convienience method provided simply code.  Most code using this
    module can simply (import db) and create a session as: db.open_session()
    and not deal with the Database object.
    """
    return Database().open_session()



if __name__ == '__main__':
    #
    # This is test code only.  Do not use this a a reference implementation.
    #
    database = Database('postgres://jortel:jortel@localhost/virtfactory')
    database.drop()
    database.create()
        
    try:
        args =\
            {'username':'jortel', 'password':'mypassword', 
             'first':'Elvis', 'last':'Prestley', 'description':'a desc', 'email':'king@hell.com'}
            
        ssn = open_session()
            
        user = User()
        user.update(args)
        ssn.save(user)
        ssn.flush()
        
        user = User.get(ssn, 1)
        session = Session()
        session.session_token = 'my token-1'
        session.user = user
        ssn.save(session)
        session = Session()
        session.session_token = 'my token-2'
        session.user = user
        ssn.save(session)
        ssn.flush()
        
        user = User.get(ssn, 1)
        for s in user.sessions:
            print s.session_token

        User.delete(ssn, 1)
    except Exception, e:
        print e.comment
        
