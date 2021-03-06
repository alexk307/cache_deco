from backends.redis.redis_backend import RedisBackend
from unittest import TestCase
from mock import Mock, patch
from random import randint


class TestRedisClient(TestCase):
    """
    Test cases for redis_backend.py
    """
    def setUp(self):
        self.address = '8.8.8.8'
        self.port = 1234
        self.redis_client = RedisBackend(self.address, self.port)
        self.recv_count = 0

    @patch('backends.redis.redis_backend.socket')
    def test_bad_send(self, mock_sock_lib):
        """
        Tests that an appropriate Exception is raised when sending
        to the socket fails
        """
        key = 'something'
        mock_socket = Mock()
        mock_sock_lib.socket.return_value = mock_socket
        mock_error_message = 'This is an error from Redis'
        mock_socket.send.side_effect = Exception(mock_error_message)

        with self.assertRaises(Exception):
            self.redis_client.get_cache(key)

        self.assertEqual(mock_socket.recv.call_count, 0)
        mock_socket.connect.assert_called_once_with(
            (self.address, self.port))
        mock_socket.send.assert_called_once_with(
            '*2\r\n$3\r\nGET\r\n$%s\r\n%s\r\n' % (len(key), key))
        mock_socket.close.assert_called_once_with()

    @patch('backends.redis.redis_backend.socket')
    def test_bad_connection(self, mock_sock_lib):
        """
        Tests that an appropriate Exception is raised when connecting to
        Redis Server fails
        """
        key = 'something'
        mock_socket = Mock()
        mock_sock_lib.socket.return_value = mock_socket
        mock_error_message = 'This is an error from Redis'
        mock_socket.connect.side_effect = Exception(mock_error_message)

        with self.assertRaises(Exception):
            self.redis_client.get_cache(key)

        self.assertEqual(mock_socket.recv.call_count, 0)
        mock_socket.connect.assert_called_once_with(
            (self.address, self.port))
        self.assertEqual(mock_socket.send.call_count, 0)
        mock_socket.close.assert_called_once_with()

    @patch('backends.redis.redis_backend.socket')
    def test_get(self, mock_sock_lib):
        """
        Tests GET
        """
        key = 'something'
        expected_value = 'something that was cached'
        mock_socket = Mock()
        mock_sock_lib.socket.return_value = mock_socket

        def socket_recv_side_effect(*args, **kwargs):
            if self.recv_count == 0:
                self.recv_count += 1
                return '\r\n%s' % expected_value
            else:
                return ""
        mock_socket.recv.side_effect = socket_recv_side_effect

        cache_response = self.redis_client.get_cache(key)

        self.assertEqual(expected_value, cache_response)
        mock_socket.recv.assert_called_with(self.redis_client.RECV_SIZE)
        self.assertEqual(mock_socket.recv.call_count, 1)
        mock_socket.connect.assert_called_once_with(
            (self.address, self.port))
        mock_socket.send.assert_called_once_with(
            '*2\r\n$3\r\nGET\r\n$%s\r\n%s\r\n' % (len(key), key))
        mock_socket.close.assert_called_once_with()

    @patch('backends.redis.redis_backend.socket')
    def test_get_large_response(self, mock_sock_lib):
        """
        Tests that the full large response is received from Redis
        """
        key = 'something'
        expected_value = 'something that was cached'
        mock_socket = Mock()
        mock_sock_lib.socket.return_value = mock_socket
        iterations = randint(10, 20)

        def socket_recv_side_effect(*args, **kwargs):
            if self.recv_count != iterations - 1:
                self.recv_count += 1
                return '\r\n%s' % (expected_value * 100)
            else:
                return ""

        mock_socket.recv.side_effect = socket_recv_side_effect
        cache_response = self.redis_client.get_cache(key)

        # self.assertEqual(expected_value, cache_response)
        mock_socket.recv.assert_called_with(self.redis_client.RECV_SIZE)
        self.assertEqual(mock_socket.recv.call_count, iterations)
        mock_socket.connect.assert_called_once_with(
            (self.address, self.port))
        mock_socket.send.assert_called_once_with(
            '*2\r\n$3\r\nGET\r\n$%s\r\n%s\r\n' % (len(key), key))
        mock_socket.close.assert_called_once_with()

    @patch('backends.redis.redis_backend.socket')
    def test_set(self, mock_sock_lib):
        """
        Tests SET
        """
        key = 'something'
        value = 'something_else'
        mock_socket = Mock()
        mock_sock_lib.socket.return_value = mock_socket

        def socket_recv_side_effect(*args, **kwargs):
            if self.recv_count == 0:
                self.recv_count += 1
                return '+OK\r\n'
            else:
                return ""
        mock_socket.recv.side_effect = socket_recv_side_effect

        cache_response = self.redis_client.set_cache(key, value)
        self.assertEqual(cache_response, '+OK')

        mock_socket.recv.assert_called_with(self.redis_client.RECV_SIZE)
        self.assertEqual(mock_socket.recv.call_count, 1)
        mock_socket.connect.assert_called_once_with(
            (self.address, self.port))
        mock_socket.send.assert_called_once_with(
            '*3\r\n$3\r\nSET\r\n$%s\r\n%s\r\n$%s\r\n%s\r\n' %
            (len(key), key, len(value), value))
        mock_socket.close.assert_called_once_with()

    @patch('backends.redis.redis_backend.socket')
    def test_delete(self, mock_sock_lib):
        """
        Tests DELETE
        """
        key = 'something'
        value = 'something_else'
        mock_socket = Mock()
        mock_sock_lib.socket.return_value = mock_socket

        mock_socket.recv.return_value = ':%s\r\n' % value

        cache_response = self.redis_client.invalidate_key(key)
        self.assertEqual(cache_response, ':%s' % value)

        mock_socket.recv.assert_called_with(self.redis_client.RECV_SIZE)
        self.assertEqual(mock_socket.recv.call_count, 1)
        mock_socket.connect.assert_called_once_with(
            (self.address, self.port))
        mock_socket.send.assert_called_once_with(
            '*2\r\n$3\r\nDEL\r\n$9\r\n%s\r\n' % key)
        mock_socket.close.assert_called_once_with()

    @patch('backends.redis.redis_backend.socket')
    def test_setex(self, mock_sock_lib):
        """
        Tests SETEX
        """
        key = 'something'
        value = 'something_else'
        expiration = 100
        mock_socket = Mock()
        mock_sock_lib.socket.return_value = mock_socket

        def socket_recv_side_effect(*args, **kwargs):
            if self.recv_count == 0:
                self.recv_count += 1
                return '+OK\r\n'
            else:
                return ""
        mock_socket.recv.side_effect = socket_recv_side_effect

        cache_response = self.redis_client.set_cache_and_expire(key, value, expiration)
        self.assertEqual(cache_response, '+OK')

        mock_socket.recv.assert_called_with(self.redis_client.RECV_SIZE)
        self.assertEqual(mock_socket.recv.call_count, 1)
        mock_socket.connect.assert_called_once_with(
            (self.address, self.port))

        expected_raw = \
            '*4\r\n$5\r\nSETEX\r\n$%s\r\n%s\r\n$%s\r\n%s\r\n$%s\r\n%s\r\n' \
            % (len(key), key, len(str(expiration)),
               expiration, len(value), value)
        mock_socket.send.assert_called_once_with(expected_raw)
        mock_socket.close.assert_called_once_with()
