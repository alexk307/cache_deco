from backends.backend_base import Backend, BackendException
import socket


class RedisBackend(Backend):

    def __init__(self, address, port):
        super(RedisBackend, self).__init__()
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
        try:
            s.connect((self.address, int(self.port)))
            s.send(command)
            response = self._recv_data(s)
            return response
        except Exception as e:
            raise BackendException(
                'Unable to make request to Redis: %s' % str(e))
        finally:
            s.close()

    def _recv_data(self, sock):
        data = ''
        while True:
            received = sock.recv(self.RECV_SIZE)
            data += received
            if len(received) <= self.RECV_SIZE:
                break
        return data

    def _build_command(self, *args):
        """
        Builds a Redis command
        :return: Raw Redis command
        """
        command_args = ['*%s' % len(args)]
        for arg in args:
            command_args.extend(['$%s' % len(str(arg)), str(arg)])
        return self.delimiter.join(command_args) + self.delimiter

    def invalidate_key(self, key):
        """
        DEL method
        :param key: The key to delete
        """
        command = self._build_command('DEL', key)
        response = self._make_request(command)
        return response.split(self.delimiter)[0]

    def get_cache(self, key):
        """
        GET method
        :param key: The key to GET
        """
        command = self._build_command('GET', key)
        response = self._make_request(command)
        return response.split(self.delimiter)[1]

    def set_cache(self, key, value, **kwargs):
        """
        SET method
        :param key: The key to SET
        :param value: The value of the key to SET
        """
        command = self._build_command('SET', key, value)
        response = self._make_request(command)
        return response.split(self.delimiter)[0]

    def set_cache_and_expire(self, key, value, expiration):
        """
        SETEX command
        :param key: The key to SET
        :param value: The value of the key to SET
        :param expiration: TTL in seconds
        """
        command = self._build_command('SETEX', key, expiration, value)
        response = self._make_request(command)
        return response.split(self.delimiter)[0]

