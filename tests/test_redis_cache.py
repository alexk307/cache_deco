from redis_cache.redis_cache import RedisCache
from unittest import TestCase
from mock import Mock, patch


class TestRedisClient(TestCase):

    def setUp(self):
        self.address = ''
        self.port = 2345


    @patch('redis_cache.redis_cache.RedisClient')
    def test_cache(self, mock_client_object):
        redis_cache = RedisCache(self.address, self.port)
        mock_client = Mock()
        mock_client_object.return_value = mock_client

        # Create a function with the decorator
        @redis_cache.cache()
        def test_function(a):
            return a

        # Call that function
        test_function()

        mock_client_object.assert_called_once_with(self.address, self.port)
