class Transport(object):

    def connect(self):
        pass

    def send_message(self, to, message):
        pass

    def send_message_wait(self, to, message, timeout=60):
        pass

class ServerTransport(Transport):

    def start(self):
        pass

    def stop(self):
        pass
    
