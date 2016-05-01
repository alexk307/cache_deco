from redis_cache.redis_cache import RedisCache
from unittest import TestCase
from mock import Mock, patch


class TestRedisClient(TestCase):

    def setUp(self):
        self.address = '10.10.10.10'
        self.port = 2345

    @patch('redis_cache.redis_cache.RedisClient')
    def test_cache_miss(self, mock_client_object):
        mock_client = Mock()
        # Simulates a cache miss
        mock_client.get.return_value = ''
        mock_client_object.return_value = mock_client
        redis_cache = RedisCache(self.address, self.port)

        # Create a function with the decorator
        @redis_cache.cache()
        def test_function(a):
            return a

        # Call that function
        test_param = 'input'
        function_response = test_function(test_param)

        mock_client_object.assert_called_once_with(self.address, self.port)
        expected_hash = str(hash('test_function' + test_param))
        mock_client.get.assert_called_once_with(expected_hash)
        mock_client.set.assert_called_once_with(expected_hash, test_param)

        # Assert that the function returns the proper data
        self.assertEqual(function_response, test_param)

    @patch('redis_cache.redis_cache.RedisClient')
    def test_cache_miss_exiration(self, mock_client_object):
        test_param = 'cache hit test'
        ttl = 100
        mock_client = Mock()
        # Simulates a cache hit
        mock_client.get.return_value = ''
        mock_client_object.return_value = mock_client
        redis_cache = RedisCache(self.address, self.port)

        # Create a function with the decorator
        @redis_cache.cache(expiration=ttl)
        def test_function(a):
            return a

        # Call that function
        function_response = test_function(test_param)
        expected_hash = str(hash('test_function' + test_param))
        mock_client_object.assert_called_once_with(self.address, self.port)
        mock_client.get.assert_called_once_with(expected_hash)
        mock_client.setex.assert_called_once_with(
            expected_hash, test_param, ttl)
        self.assertEqual(mock_client.set.call_count, 0)
        self.assertEqual(function_response, test_param)

    @patch('redis_cache.redis_cache.RedisClient')
    def test_cache_hit(self, mock_client_object):
        test_param = 'cache hit test'
        mock_client = Mock()
        # Simulates a cache hit
        mock_client.get.return_value = test_param
        mock_client_object.return_value = mock_client
        redis_cache = RedisCache(self.address, self.port)

        # Create a function with the decorator
        @redis_cache.cache()
        def test_function(a):
            return a

        # Call that function
        function_response = test_function(test_param)
        expected_hash = str(hash('test_function' + test_param))
        mock_client_object.assert_called_once_with(self.address, self.port)
        mock_client.get.assert_called_once_with(expected_hash)
        self.assertEqual(mock_client.set.call_count, 0)
        self.assertEqual(function_response, test_param)
