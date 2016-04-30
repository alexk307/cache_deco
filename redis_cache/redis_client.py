import socket


class RedisClient(object):
    """
    Client to communicate with the Redis Server
    """

    def __init__(self, address, port):
        self.delimiter = '\r\n'
        self.address = address
        self.port = port
        self.RECV_SIZE = 2048

    def _make_request(self, command):
        """
        Makes the request to the Redis Server
        :param command: Raw Redis command
        :return: Response from Redis Server
        """
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.address, int(self.port)))
        s.send(command)
        response = s.recv(self.RECV_SIZE)
        s.close()
        return response

    def _build_command(self, *args):
        """
        Builds a Redis command
        :return: Raw Redis command
        """
        command_args = ['*%s' % len(args)]
        for arg in args:
            command_args.extend(['$%s' % len(str(arg)), str(arg)])
        return self.delimiter.join(command_args) + self.delimiter

    def get(self, key):
        """
        GET method
        :param key: The key to GET
        """
        command = self._build_command('GET', key)
        response = self._make_request(command)
        return response.split(self.delimiter)[1]

    def set(self, key, value, **kwargs):
        """
        SET method
        :param key: The key to SET
        :param value: The value of the key to SET
        """
        command = self._build_command('SET', key, value)
        response = self._make_request(command)
        return response.split(self.delimiter)[0]

    def setex(self, key, value, expiration):
        """
        SETEX command
        :param key: The key to SET
        :param value: The value of the key to SET
        :param expiration: TTL in seconds
        """
        command = self._build_command('SETEX', key, expiration, value)
        response = self._make_request(command)
        return response.split(self.delimiter)[0]
