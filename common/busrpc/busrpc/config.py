SERVER_NAME = "busrpc.server.name"
INSTANCE_NAME = "busrpc.instance"

def _parse_name_value(line):
    parts = line.split("=")
    return parts[0], parts[1]

class DeploymentConfig:

    """ Parses service deployment config files"""

    def __init__(self, filename):
        self.instances = {}
        self.server_name = None
        self.config_values = {}
        f = None
        try:
            f = open(filename, "r")
            for line in f:
                self.parse(line)
        finally:
            if not f == None:
                f.close()

    def parse(self, line):
        line = line.replace("\n", "")
        if line.startswith("#"):
            pass
        name, value = _parse_name_value(line)
        if name == SERVER_NAME:
            self.server_name = value.replace("\"", "")
        elif name.startswith(INSTANCE_NAME):
            self.instances[name] = value
        else:
            self.config_values[name] = value

    def get_value(self, entry_name, default=None):
        if self.config_values.has_key(entry_name):
            return self.config_values[entry_name]
        else:
            return default

    def get_value_list(self, entry_name, default=None):
        value = self.get_value(entry_name, default=default)
        if not value == None:
            return value.split(',')
        else:
            return default

    def get_value_number(self, entry_name, default=None):
        value = self.get_value(entry_name, default=default)
        if not value == None and not value == "":
            try:
                return int(value)
            except ValueError:
                return float(value)
        else:
            return value
