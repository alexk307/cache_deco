from redis_cache.redis_client import RedisClient
from unittest import TestCase
from mock import Mock, patch


class TestRedisClient(TestCase):
    """
    Test cases for redis_client.py
    """

    def setUp(self):
        self.address = '8.8.8.8'
        self.port = 1234
        self.redis_client = RedisClient(self.address, self.port)

    @patch('redis_cache.redis_client.socket')
    def test_get(self, mock_sock_lib):
        """
        Tests GET
        """
        key = 'something'
        expected_value = 'something that was cached'
        mock_socket = Mock()
        mock_sock_lib.socket.return_value = mock_socket
        mock_socket.recv.return_value = '\r\n%s' % expected_value

        cache_response = self.redis_client.get(key)

        self.assertEqual(expected_value, cache_response)
        mock_socket.recv.assert_called_once_with(self.redis_client.RECV_SIZE)
        mock_socket.connect.assert_called_once_with(
            (self.address, self.port))
        mock_socket.send.assert_called_once_with(
            '*2\r\n$3\r\nGET\r\n$%s\r\n%s\r\n' % (len(key), key))
        mock_socket.close.assert_called_once_with()

    @patch('redis_cache.redis_client.socket')
    def test_set(self, mock_sock_lib):
        """
        Tests SET
        """
        key = 'something'
        value = 'something_else'
        mock_socket = Mock()
        mock_sock_lib.socket.return_value = mock_socket
        mock_socket.recv.return_value = '+OK\r\n'

        cache_response = self.redis_client.set(key, value)
        self.assertEqual(cache_response, '+OK')

        mock_socket.recv.assert_called_once_with(self.redis_client.RECV_SIZE)
        mock_socket.connect.assert_called_once_with(
            (self.address, self.port))
        mock_socket.send.assert_called_once_with(
            '*3\r\n$3\r\nSET\r\n$%s\r\n%s\r\n$%s\r\n%s\r\n' %
            (len(key), key, len(value), value))
        mock_socket.close.assert_called_once_with()

    @patch('redis_cache.redis_client.socket')
    def test_setex(self, mock_sock_lib):
        """
        Tests SETEX
        """
        key = 'something'
        value = 'something_else'
        expiration = 100
        mock_socket = Mock()
        mock_sock_lib.socket.return_value = mock_socket
        mock_socket.recv.return_value = '+OK\r\n'

        cache_response = self.redis_client.setex(key, value, expiration)
        self.assertEqual(cache_response, '+OK')

        mock_socket.recv.assert_called_once_with(self.redis_client.RECV_SIZE)
        mock_socket.connect.assert_called_once_with(
            (self.address, self.port))

        expected_raw = \
            '*4\r\n$5\r\nSETEX\r\n$%s\r\n%s\r\n$%s\r\n%s\r\n$%s\r\n%s\r\n' \
            % (len(key), key, len(str(expiration)),
               expiration, len(value), value)
        mock_socket.send.assert_called_once_with(expected_raw)
        mock_socket.close.assert_called_once_with()
