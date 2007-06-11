import os
import threading
import cPickle
from Crypto.Util.randpool import RandomPool
from Crypto.Cipher import Blowfish
from Crypto.Hash import SHA

class CryptoException(Exception):

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return repr(self.message)    

class CertManager(object):

    def __init__(self, keydir, hostname):
        self.keydir = keydir
        self.hostname = hostname
        if not self.keydir.endswith('/'):
            self.keydir += '/'
        self.private_keys = []
        self.pub_keys = {}
        self.private_key_lock = threading.RLock()
        self.pub_key_lock = threading.RLock()

    def decrypt_message(self, message):
        secure_host, encrypted_message = self._parse_secure_message(message)
        if secure_host == None:
            return message
        else:
            key = None
            try:
                key = self.load_pub_key(secure_host)
                retval = key.decrypt(encrypted_message)
                return retval.strip()
            finally:
                if not key == None:
                    self.release_pub_key(secure_host, key)

    def encrypt_message(self, host, message):
        key = None
        try:
            while not len(message) % 8 == 0:
                message += ' '
            key = self.load_private_key()
            encrypted_message = key.encrypt(message)
            composed_message = ''.join(['secure-host:',
                                        host,
                                        '\n\n',
                                        encrypted_message])
            return composed_message
        finally:
            if not key == None:
                self.release_private_key(key)
        

    def load_private_key(self):
        key = None
        try:
            self.private_key_lock.acquire()
            if len(self.private_keys) > 0:
                key = self.private_keys.pop()
            else:
                key = self._load_private_key()
        finally:
            self.private_key_lock.release()
        return key

    def release_private_key(self, key):
        try:
            self.private_key_lock.acquire()
            self.private_keys.append(key)
        finally:
            self.private_key_lock.release()

    def load_pub_key(self, host):
        key = None
        try:
            self.pub_key_lock.acquire()
            if self.pub_keys.has_key(host):
                keys = self.pub_keys[host]
                if len(keys) > 0:
                    key = keys.pop()
            if key == None:
                key = self._load_pub_key(host)
        finally:
            self.pub_key_lock.release()
        return key

    def release_pub_key(self, host, key):
        try:
            self.pub_key_lock.acquire()
            if not self.pub_keys.has_key(host):
                self.pub_keys[host] = []
            self.pub_keys[host].append(key)
        finally:
            self.pub_key_lock.release()

    def _load_pub_key(self, host):
        key = None
        file_name = self.keydir + host + '.key'
        if os.path.lexists(file_name):
            f = file(file_name)
            unpickler = cPickle.Unpickler(f)
            try:
                seed = unpickler.load()
                key = Blowfish.new(seed)
            finally:
                f.close()
        return key

    def _load_private_key(self):
        key = self._load_pub_key(self.hostname)
        if key == None:
            self._setup_dir(self.keydir)
            seed = self._generate_seed(8192)
            key = Blowfish.new(seed)
            file_name = self.keydir + self.hostname + '.key'
            f = file(file_name)
            pickler = cPickle.Pickler(f)
            try:
                pickler.dump(seed)
                f.flush()
            finally:
                f.close()
        return key
            

    def _generate_seed(self, size):
        rp = RandomPool()
        for i in range(7):
            m = SHA.new()
            temp_seed = rp.get_bytes(size)
            m.update(tempseed)
            rp.add_event(m.hexdigest())
        return rp.get_bytes(size)
    
    def _setup_dir(self, dirpath):
        os.makedirs(dirpath)
        
    def _parse_secure_message(self, message):
        parts = message.split('\n\n')
        secure_host = None
        message = None
        if len(parts) > 1:
            if parts[0].startswith('secure-host:'):
                line = parts[0].split(':')
                if len(line) > 1:
                    secure_host = line[1].strip()
                    message = parts[1]
        return secure_host, message
