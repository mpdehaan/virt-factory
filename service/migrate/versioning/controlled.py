from sqlalchemy import *
import sqlalchemy
from base import *
from migrate.versioning.repository import Repository
from migrate.versioning.version import VerNum
from migrate.versioning import exceptions

class ControlledSchema(object):
    """A database under version control"""
    #def __init__(self,engine,repository=None):
    def __init__(self,engine,repository):
        if type(repository) is str:
            repository=Repository(repository)
        self.engine = engine
        self.repository = repository
        self.meta=BoundMetaData(engine)
        #if self.repository is None:
        #   self._get_repository()
        self._load()
    
    def __eq__(self,other):
        return (self.repository is other.repository \
            and self.version == other.version)
    
    def _load(self):
        """Load controlled schema version info from DB"""
        tname = self.repository.version_table
        self.meta=BoundMetaData(self.engine)
        if not hasattr(self,'table') or self.table is None:
            try:
                self.table=Table(tname,self.meta,autoload=True)
            except (exceptions.NoSuchTableError):
                raise exceptions.DatabaseNotControlledError(tname)
        # TODO?: verify that the table is correct (# cols, etc.)
        result = self.engine.execute(self.table.select(),)
        data = list(result)[0]
        # TODO?: exception if row count is bad
        # TODO: check repository id, exception if incorrect
        self.version = data['version']
    
    def _get_repository(self):
        """Given a database engine, try to guess the repository"""
        # TODO: no guessing yet; for now, a repository must be supplied
        raise NotImplementedError()
    
    @classmethod
    def create(cls,engine,repository,version=None):
        """Declare a database to be under a repository's version control"""
        # Confirm that the version # is valid: positive, integer, exists in repos
        if type(repository) is str:
            repository=Repository(repository)
        version = cls._validate_version(repository,version)
        table=cls._create_table_version(engine,repository,version)
        # TODO: history table
        # Load repository information and return
        return cls(engine,repository)
    
    @classmethod
    def _validate_version(cls,repository,version):
        """Ensures this is a valid version number for this repository
        If invalid, raises cls.InvalidVersionError
        Returns a valid version number
        """
        if version is None:
            version=0
        try:
            version = VerNum(version) # raises valueerror
            if version < 0 or version > repository.latest:
                raise ValueError()
        except ValueError:
            raise exceptions.InvalidVersionError(version)
        return version
    
    @classmethod
    def _create_table_version(cls,engine,repository,version):
        """Creates the versioning table in a database"""
        # Create tables
        tname = repository.version_table
        meta=BoundMetaData(engine)
        try:
            table=Table(tname,meta,
                #Column('repository_id',String,primary_key=True), # MySQL needs a length
                Column('repository_id',String(255),primary_key=True),
                Column('repository_path',String),
                Column('version',Integer),
            )
            table.create()
        except (sqlalchemy.exceptions.ArgumentError,sqlalchemy.exceptions.SQLError):
            # The table already exists
            raise exceptions.DatabaseAlreadyControlledError()
        # Insert data
        engine.execute(table.insert(),repository_id=repository.id,
            repository_path=repository.path,version=int(version))
        return table

    def drop(self):
        """Remove version control from a database"""
        try:
            self.table.drop()
        except (sqlalchemy.exceptions.SQLError):
            raise exceptions.DatabaseNotControlledError(str(self.table))
    
    def _engine_db(self,engine):
        """Returns the database name of an engine - 'postgres','sqlite'..."""
        # TODO: This is a bit of a hack...
        return str(engine.dialect.__module__).split('.')[-1]

    def changeset(self,version=None):
        database = self._engine_db(self.engine)
        start_ver = self.version
        changeset = self.repository.changeset(database,start_ver,version)
        return changeset
    
    def runchange(self,ver,change,step):
        startver = ver
        endver = ver + step
        # Current database version must be correct! Don't run if corrupt!
        if self.version != startver:
            raise exceptions.InvalidVersionError("%s is not %s"%(self.version,startver))
        # Run the change
        change.run(self.engine,step)
        # Update/refresh database version
        update = self.table.update(self.table.c.version == int(startver))
        self.engine.execute(update, version=int(endver))
        self._load()
        
    def upgrade(self,version=None):
        """Upgrade (or downgrade) to a specified version, or latest version"""
        changeset = self.changeset(version)
        for ver,change in changeset:
            self.runchange(ver,change,changeset.step)
