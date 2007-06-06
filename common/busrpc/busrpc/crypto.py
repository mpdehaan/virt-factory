import os
import threading
import base64
from M2Crypto import RSA

class CryptoException(Exception):

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return repr(self.message)    

class CertManager(object):

    def __init__(self, certdir, hostname, password):
        self.pub_keys = {}
        self.pub_key_lock = threading.RLock()
        self.private_keys = []
        self.private_key_lock = threading.RLock()
        self.keystore_password = password
        self.hostname = hostname
        if not certdir.endswith('/'):
            certdir += '/'
        self.private_key_dir = os.path.realpath(certdir + 'private/') + '/'
        self.public_key_dir = os.path.realpath(certdir + 'public/') + '/'
        self.private_key_file = self.private_key_dir + self.hostname + '.pem'
        if not os.path.lexists(self.private_key_dir):
            self._setup_dir(self.private_key_dir)
        if not os.path.lexists(self.public_key_dir):
            self._setup_dir(self.public_key_dir)
        self._gen_private_key()

    def decrypt_message(self, message):
        parts = message.split("\n\n")
        secure_host, encrypted_message = self._parse_secure_message(message)
        if secure_host == None:
            return message
        else:
            key = None
            try:
                key = self.load_pub_key(secure_host)
                retval = key.public_decrypt(base64.decodestring(encrypted_message), RSA.pkcs1_padding)
                print 'Returning:\n%s' % retval
                return retval
            finally:
                if not key == None:
                    self.release_pub_key(secure_host, key)

    def encrypt_message(self, host, message):
        key = None
        try:
            key = self.load_private_key()
            encrypted_message = base64.encodestring(key.private_encrypt(message, RSA.pkcs1_padding))
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
        file_name = self.public_key_dir + host + '.pem'
        return RSA.load_pub_key(file_name)

    def _load_private_key(self):
        return RSA.load_key(self.private_key_file, callback=self._dummy_password_callback)
    
    def _setup_dir(self, dirpath):
        os.makedirs(dirpath)

    def _gen_private_key(self):
        if not os.path.lexists(self.private_key_file):
            rsa = RSA.gen_key(4096, 65537, callback=self._dummy_gen_callback)
            rsa.save_key(self.private_key_file, callback=self._dummy_password_callback)
            rsa.save_pub_key(self.public_key_dir + self.hostname + '.pem')
        
    def _dummy_password_callback(self, arg):
        return self.keystore_password
    
    def _dummy_gen_callback(self, arg):
        pass

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
