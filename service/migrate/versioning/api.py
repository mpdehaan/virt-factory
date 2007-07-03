"""An external API to the versioning system
Used by the shell utility; could also be used by other scripts
"""
from migrate.versioning.base import *
from migrate.versioning.repository import *
from migrate.versioning.repository import manage as repository_manage
from migrate.versioning.controlled import *
from migrate.versioning import exceptions
import script as script_ # Conflicts with a command
import sys
import stat
import inspect

__all__=[#'KnownError','UsageError',
'help',
'create',
'script',
'commit',
'version',
'source',
'version_control',
'db_version',
'upgrade',
'downgrade',
'drop_version_control',
'manage',
'test',
]

def help(cmd=None,**opts):
    """%prog help COMMAND

    Displays help on a given command.
    """
    if cmd is None:
        raise exceptions.UsageError(None)
    try:
        func = globals()[cmd]
    except:
        raise exceptions.UsageError("'%s' isn't a valid command. Try 'help COMMAND'"%cmd)
    ret = func.__doc__
    if sys.argv[0]:
        ret = ret.replace('%prog',sys.argv[0]) 
    return ret

def create(repository,name,**opts):
    """%prog create REPOSITORY_PATH NAME [--table=TABLE]

    Create an empty repository at the specified path.

    You can specify the version_table to be used; by default, it is '_version'.
    This table is created in all version-controlled databases.
    """
    try:
        rep=Repository.create(repository,name,**opts)
    except exceptions.PathFoundError,e:
        raise exceptions.KnownError("The path %s already exists"%e.args[0])

def script(path,**opts):
    """%prog script PATH

    Create an empty change script at the specified path. 
    """
    try:
        script_.PythonFile.create(path,**opts)
    except exceptions.PathFoundError,e:
        raise exceptions.KnownError("The path %s already exists"%e.args[0])

def commit(script,repository,database=None,operation=None,version=None,**opts):
    """%prog commit SCRIPT_PATH.py REPOSITORY_PATH [VERSION]

    %prog commit SCRIPT_PATH.sql REPOSITORY_PATH DATABASE OPERATION [VERSION]

    Commit a script to this repository. The committed script is added to the
    repository, and the file disappears.

    Once a script has been committed, you can use it to upgrade a database with
    the 'upgrade' command.

    If a version is given, that version will be replaced instead of creating a
    new version.

    Normally, when writing change scripts in Python, you'll use the first form
    of this command (DATABASE and OPERATION aren't specified). If you write
    change scripts as .sql files, you'll need to specify DATABASE ('postgres',
    'mysql', 'oracle', 'sqlite'...) and OPERATION ('upgrade' or 'downgrade').
    You may commit multiple .sql files under the same version to complete
    functionality for a particular version::

        %prog commit upgrade.postgres.sql /repository/path postgres upgrade 1
        %prog commit downgrade.postgres.sql /repository/path postgres downgrade 1
        %prog commit upgrade.sqlite.sql /repository/path sqlite upgrade 1
        %prog commit downgrade.sqlite.sql /repository/path sqlite downgrade 1
        [etc...]
    """
    if (database is not None) and (operation is None) and (version is None):
        # Version was supplied as a positional
        version = database
        database = None
    
    repos = Repository(repository)
    repos.commit(script,version,database=database,operation=operation)

def test(script,repository,url=None,**opts):
    """%prog test SCRIPT_PATH REPOSITORY_PATH URL [VERSION]
    """
    engine=create_engine(url)
    controlled=ControlledSchema(engine,repository)
    script = script_.PythonFile(script)
    # Upgrade
    print "Upgrading...",
    try:
        script.run(engine,1)
    except:
        print "ERROR"
        raise
    print "done"

    print "Downgrading...",
    try:
        script.run(engine,-1)
    except:
        print "ERROR"
        raise
    print "done"
    print "Success"

def version(repository,**opts):
    """%prog version REPOSITORY_PATH

    Display the latest version available in a repository.
    """
    repos=Repository(repository)
    return repos.latest

def source(version,dest=None,repository=None,**opts):
    """%prog source VERSION [DESTINATION] --repository=REPOSITORY_PATH

    Display the Python code for a particular version in this repository.
    Save it to the file at DESTINATION or, if omitted, send to stdout. 
    """
    if repository is None:
        raise exceptions.UsageError("A repository must be specified")
    repos=Repository(repository)
    ret=repos.version(version).script().source()
    if dest is not None:
        dest=open(dest,'w')
        dest.write(ret)
        ret=None
    return ret

def version_control(url,repository,version=None,**opts):
    """%prog version_control URL REPOSITORY_PATH [VERSION]

    Mark a database as under this repository's version control.
    Once a database is under version control, schema changes should only be
    done via change scripts in this repository. 

    This creates the table version_table in the database.

    The url should be any valid SQLAlchemy connection string.

    By default, the database begins at version 0 and is assumed to be empty.
    If the database is not empty, you may specify a version at which to begin
    instead. No attempt is made to verify this version's correctness - the
    database schema is expected to be identical to what it would be if the
    database were created from scratch. 
    """
    engine=create_engine(url)
    ControlledSchema.create(engine,repository,version)

def db_version(url,repository,**opts):
    """%prog db_version URL REPOSITORY_PATH

    Show the current version of the repository with the given connection
    string, under version control of the specified repository. 

    The url should be any valid SQLAlchemy connection string.
    """
    engine=create_engine(url)
    controlled=ControlledSchema(engine,repository)
    return controlled.version

def upgrade(url,repository,version=None,**opts):
    """%prog upgrade URL REPOSITORY_PATH [VERSION] [--preview_py|--preview_sql]

    Upgrade a database to a later version. 
    This runs the upgrade() function defined in your change scripts.

    By default, the database is updated to the latest available version. You
    may specify a version instead, if you wish.

    You may preview the Python or SQL code to be executed, rather than actually
    executing it, using the appropriate 'preview' option.
    """
    err = "Cannot upgrade a database of version %s to version %s. "\
        "Try 'downgrade' instead."
    return _migrate(url,repository,version,upgrade=True,err=err,**opts)

def downgrade(url,repository,version,**opts):
    """%prog downgrade URL REPOSITORY_PATH VERSION [--preview_py|--preview_sql]

    Downgrade a database to an earlier version.
    This is the reverse of upgrade; this runs the downgrade() function defined
    in your change scripts.

    You may preview the Python or SQL code to be executed, rather than actually
    executing it, using the appropriate 'preview' option.
    """
    err = "Cannot downgrade a database of version %s to version %s. "\
        "Try 'upgrade' instead."
    return _migrate(url,repository,version,upgrade=False,err=err,**opts)

def _migrate(url,repository,version,upgrade,err,**opts):
    engine=create_engine(url)
    controlled=ControlledSchema(engine,repository)
    version = _migrate_version(controlled,version,upgrade,err)

    changeset = controlled.changeset(version)
    for ver,change in changeset:
        nextver = ver + changeset.step
        print '%s -> %s... '%(ver,nextver),
        if opts.get('preview_sql'):
            print
            print change.log
        elif opts.get('preview_py'):
            source_ver = max(ver,nextver)
            module = controlled.repository.version(source_ver).script().module
            funcname = upgrade and "upgrade" or "downgrade"
            func = getattr(module,funcname)
            print
            print inspect.getsource(module.upgrade)
        else:
            controlled.runchange(ver,change,changeset.step)
            print 'done'

def _migrate_version(controlled,version,upgrade,err):
    if version is None:
        return version
    # Version is specified: ensure we're upgrading in the right direction
    # (current version < target version for upgrading; reverse for down)
    version = VerNum(version)
    cur = controlled.version
    if upgrade is not None:
        if upgrade:
            direction = cur <= version
        else:
            direction = cur >= version
        if not direction:
            raise exceptions.KnownError(err%(cur,version))
    return version

def drop_version_control(url,repository,**opts):
    """%prog drop_version_control URL REPOSITORY_PATH

    Removes version control from a database.
    """
    engine=create_engine(url)
    controlled=ControlledSchema(engine,repository)
    controlled.drop()

def manage(file,**opts):
    """%prog manage FILENAME VARIABLES...

    Creates a script that runs Migrate with a set of default values. 

    For example::

        %prog manage manage.py --repository=/path/to/repository --url=sqlite:///project.db

    would create the script manage.py. The following two commands would then
    have exactly the same results::

        python manage.py version
        %prog version --repository=/path/to/repository
    """
    return repository_manage(file,**opts)

