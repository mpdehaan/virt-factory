"""Extensions to SQLAlchemy for altering existing tables.
At the moment, this isn't so much based off of ANSI as much as things that just
happen to work with multiple databases.
"""
from sqlalchemy import *
from sqlalchemy import ansisql
from migrate.changeset import constraint,util,exceptions

class RawAlterTableVisitor(object):
    """Common operations for 'alter table' statements"""
    def _to_table(self,param):
        if isinstance(param,(Column,Index,schema.Constraint)):
            ret = param.table
        else:
            ret = param
        return ret
    def _to_table_name(self,param):
        ret = self._to_table(param)
        if isinstance(ret,Table):
            ret = ret.fullname
        return ret

    def start_alter_table(self,param):
        table = self._to_table(param)
        table_name = self._to_table_name(table)
        self.append("\nALTER TABLE %s "%table_name)
        return table

    def _pk_constraint(self,table,column,status):
        """Create a primary key constraint from a table, column
        Status: true if the constraint is being added; false if being dropped
        """
        if isinstance(column,basestring):
            column = getattr(table.c,name)

        ret = constraint.PrimaryKeyConstraint(*table.primary_key)
        if status:
            # Created PK
            ret.c.append(column)
        else:
            # Dropped PK
            #cons.remove(col)
            names = [c.name for c in cons.c]
            index = names.index(col.name)
            del ret.c[index]

        # Allow explicit PK name assignment
        if isinstance(pk,basestring):
            ret.name = pk
        return ret

class AlterTableVisitor(engine.SchemaIterator,RawAlterTableVisitor):
    """Common operations for 'alter table' statements"""
        
class ANSIColumnGenerator(AlterTableVisitor,ansisql.ANSISchemaGenerator):
    """Extends ansisql generator for column creation (alter table add col)"""
    def visit_column(self,column):
        """Create a column (table already exists); #32"""
        table = self.start_alter_table(column)
        self.append(" ADD ")
        pks = table.primary_key
        colspec = self.get_column_specification(column)
        self.append(colspec)
        self.execute()
        #if column.primary_key:
        #    cons = self._pk_constraint(table,column,True)
        #    cons.drop()
        #    cons.create()

    def visit_table(self,table):
        pass

class ANSIColumnDropper(AlterTableVisitor):
    """Extends ansisql dropper for column dropping (alter table drop col)"""
    def visit_column(self,column):
        """Drop a column; #33"""
        table = self.start_alter_table(column)
        self.append(" DROP COLUMN %s"%column.name)
        self.execute()
        #if column.primary_key:
        #    cons = self._pk_constraint(table,column,False)
        #    cons.create()

class ANSISchemaChanger(AlterTableVisitor,ansisql.ANSISchemaGenerator):
    """Manages changes to existing schema elements. 
    Note that columns are schema elements; "alter table add column" is in
    SchemaGenerator.

    All items may be renamed. Columns can also have many of their properties -
    type, for example - changed.

    Each function is passed a tuple, containing (object,name); where object 
    is a type of object you'd expect for that function (ie. table for
    visit_table) and name is the object's new name. NONE means the name is
    unchanged.
    """
    def visit_table(self,param):
        """Rename a table; #38. Other ops aren't supported."""
        table,newname = param
        self.start_alter_table(table)
        self.append("RENAME TO %s"%newname)
        self.execute()

    def visit_column(self,delta):
        """Rename/change a column; #34/#35"""
        # ALTER COLUMN is implemented as several ALTER statements
        keys = delta.keys()
        if 'type' in keys:
            self._run_subvisit(delta,self._visit_column_type)
        if 'nullable' in keys:
            self._run_subvisit(delta,self._visit_column_nullable)
        if 'default' in keys:
            self._run_subvisit(delta,self._visit_column_default)
        #if 'primary_key' in keys:
        #    #self._run_subvisit(delta,self._visit_column_primary_key)
        #    self._visit_column_primary_key(delta)
        #if 'foreign_key' in keys:
        #    self._visit_column_foreign_key(delta)
        if 'name' in keys:
            self._run_subvisit(delta,self._visit_column_name)
    def _run_subvisit(self,delta,func,col_name=None,table_name=None):
        if table_name is None:
            table_name = delta.table_name
        if col_name is None:
            col_name = delta.current_name
        ret = func(table_name,col_name,delta)
        self.execute()
        return ret

    def _visit_column_foreign_key(self,delta):
        table = delta.table
        column = getattr(table.c,delta.current_name)
        cons = constraint.ForeignKeyConstraint(column,autoload=True)
        fk = delta['foreign_key']
        if fk:
            # For now, cons.columns is limited to one column:
            # no multicolumn FKs
            column.foreign_key = ForeignKey(*cons.columns)
        else:
            column_foreign_key = None
        cons.drop()
        cons.create()
    def _visit_column_primary_key(self,delta):
        table = delta.table
        col = getattr(table.c,delta.current_name)
        pk = delta['primary_key']
        cons = self._pk_constraint(table,col,pk)
        cons.drop()
        cons.create()
    def _visit_column_nullable(self,table_name,col_name,delta):
        nullable = delta['nullable']
        table = self._to_table(delta)
        self.start_alter_table(table_name)
        self.append("ALTER COLUMN %s "%col_name)
        if nullable:
            self.append("DROP NOT NULL")
        else:
            self.append("SET NOT NULL")
    def _visit_column_default(self,table_name,col_name,delta):
        default = delta['default']
        # Default must be a PassiveDefault; else, ignore
        # (Non-PassiveDefaults are managed by the app, not the db)
        if default is not None:
            if not isinstance(default,PassiveDefault):
                return
        # Dummy column: get_col_default_string needs a column for some reason
        dummy = Column(None,None,default=default)
        default_text = self.get_column_default_string(dummy)
        self.start_alter_table(table_name)
        self.append("ALTER COLUMN %s "%col_name)
        if default_text is not None:
            self.append("SET DEFAULT %s"%default_text)
        else:
            self.append("DROP DEFAULT")
    def _visit_column_type(self,table_name,col_name,delta):
        type = delta['type']
        if not isinstance(type,types.AbstractType):
            # It's the class itself, not an instance... make an instance
            type = type()
        type_text = type.engine_impl(self.engine).get_col_spec()
        self.start_alter_table(table_name)
        self.append("ALTER COLUMN %s TYPE %s"%(col_name,type_text))
    def _visit_column_name(self,table_name,col_name,delta):
        new_name = delta['name']
        self.start_alter_table(table_name)
        self.append("RENAME COLUMN %s TO %s"%(col_name,new_name))

    def visit_index(self,param):
        """Rename an index; #36"""
        index,newname = param
        #self.start_alter_table(index)
        #self.append("RENAME INDEX %s TO %s"%(index.name,newname))
        self.append("ALTER INDEX %s RENAME TO %s"%(index.name,newname))
        self.execute()


class ANSIConstraintCommon(RawAlterTableVisitor):
    """
    Migrate's constraints require a separate creation function from SA's: 
    Migrate's constraints are created independently of a table; SA's are
    created at the same time as the table.
    """
    def get_constraint_name(self,cons):
        if cons.name is not None:
            ret = cons.name
        else:
            ret = cons.name = cons.autoname()
        return ret

class ANSIConstraintGenerator(ANSIConstraintCommon):
    def get_constraint_specification(self,cons,**kwargs):
        if isinstance(cons,PrimaryKeyConstraint):
            col_names = ','.join([i.name for i in cons.columns])
            ret = "PRIMARY KEY (%s)"%col_names
            if cons.name:
                # Named constraint
                ret = ("CONSTRAINT %s "%cons.name)+ret
        elif isinstance(cons,ForeignKeyConstraint):
            params = dict(
                columns=','.join([c.name for c in cons.columns]),
                reftable=cons.reftable,
                referenced=','.join([c.name for c in cons.referenced]),
                name=self.get_constraint_name(cons),
            )
            ret = "CONSTRAINT %(name)s FOREIGN KEY (%(columns)s) "\
                "REFERENCES %(reftable)s (%(referenced)s)"%params
        else:
            raise exceptions.InvalidConstraintError(cons)
        return ret
    def _visit_constraint(self,constraint):
        table = self.start_alter_table(constraint)
        self.append("ADD ")
        spec = self.get_constraint_specification(constraint)
        self.append(spec)
        self.execute()

    def visit_migrate_primary_key_constraint(self,*p,**k):
        return self._visit_constraint(*p,**k)

    def visit_migrate_foreign_key_constraint(self,*p,**k):
        return self._visit_constraint(*p,**k)

class ANSIConstraintDropper(ANSIConstraintCommon):
    def _visit_constraint(self,constraint):
        self.start_alter_table(constraint)
        self.append("DROP CONSTRAINT ")
        self.append(self.get_constraint_name(constraint))
        self.execute()

    def visit_migrate_primary_key_constraint(self,*p,**k):
        return self._visit_constraint(*p,**k)

    def visit_migrate_foreign_key_constraint(self,*p,**k):
        return self._visit_constraint(*p,**k)

class ANSIDialectChangeset(object):
    columngenerator = ANSIColumnGenerator
    columndropper = ANSIColumnDropper
    schemachanger = ANSISchemaChanger

    def reflectconstraints(self,connection,table_name):
        raise NotImplementedError()

def _patch():
    ansisql.ANSIDialect.__bases__ += (ANSIDialectChangeset,)
    ansisql.ANSISchemaGenerator.__bases__ += (ANSIConstraintGenerator,)
    ansisql.ANSISchemaDropper.__bases__ += (ANSIConstraintDropper,)
