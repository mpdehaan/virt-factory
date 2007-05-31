"""
Virt-factory backend code.

Copyright 2006, Red Hat, Inc

This software may be freely redistributed under the terms of the GNU
general public license.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
"""

from server.codes import *
import string
import os

class FieldValidator:
    """
    The field validator provides simple dictionary validation.
    """
    def __init__(self, data={}):
        self.data = data
        
    def verify_required(self, keyset):
        violations = {}
        for key in keyset:
            if key not in self.data:
                violations[key] = REASON_REQUIRED
        if len(violations) > 0:
            raise InvalidArgumentsException(invalid_fields=violations)
        
    def verify_int(self, positive=True, strict=False, *keyset):
        violations = {}
        for key in keyset:
            try:
                if strict:
                    n = int(self.data.get(key, None))
                else:
                    n = int(self.data.get(key, 0))
                if positive:
                    if n < 0:
                        violations[key] = REASON_RANGE
            except:
                violations[key] = REASON_FORMAT
        if len(violations) > 0:
            raise InvalidArgumentsException(invalid_fields=violations)
        
    def verify_enum(self, key, values, strict=False):
        try:
            if strict:
                value = self.data.get(key, None)
            else:
                value = self.data.get(key, values[0])
            if value not in values:
                raise Exception
        except:
            violation = { key:REASON_RANGE }
            raise InvalidArgumentsException(invalid_fields=(violation,))
        
    def verify_file(self, *keyset):
        violations = {}
        for key in keyset:
            name = self.data.get(key, None)
            if name is None: continue    
            if not os.path.isfile(name):
                violations[name] = REASON_NOFILE
        if len(violations) > 0:
            raise InvalidArgumentsException(invalid_fields=violations)     

    def verify_printable(self, *keyset):
        violations = {}
        for key in keyset:
            s = self.data.get(key, None)
            if s is None: continue
            try:
                for letter in str(s):
                    if letter not in string.printable:
                        raise Exception
            except:
                violations[stringy] = REASON_FORMAT
        if len(violations) > 0:
            raise InvalidArgumentsException(invalid_fields=violations)      