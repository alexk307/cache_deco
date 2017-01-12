from cache_deco import Cache, DEFAULT_EXPIRATION
from backends.backend_base import Backend, BackendException
from unittest import TestCase
from mock import Mock
from inputs import SimpleObject
import collections
import pickle


class TestRedisCache(TestCase):
    """
    Test cases for redis_cache.py
    """

    def setUp(self):
        self.address = '10.10.10.10'
        self.port = 2345

    def test_cache_miss(self):
        """
        Tests a cache miss
        """
        mock_client = Mock()
        # Simulates a cache miss
        redis_cache = Cache(Backend())
        redis_cache.backend = mock_client
        redis_cache.backend.get_cache.return_value = ''

        # Create a function with the decorator
        @redis_cache.cache()
        def test_function(a):
            return a

        def cache_key_for(*args, **kwargs):
            return redis_cache._generate_cache_key(test_function, args, kwargs)

        # Call that function
        test_param = 'input'
        function_response = test_function(test_param)

        expected_hash = cache_key_for(test_param)
        mock_client.get_cache.assert_called_once_with(expected_hash)
        mock_client.set_cache_and_expire.assert_called_once_with(
            expected_hash, pickle.dumps(test_param), DEFAULT_EXPIRATION)

    def test_cache_miss_kwargs(self):
        """
        Tests a cache miss against a function with kwargs
        """
        mock_client = Mock()
        # Simulates a cache miss
        redis_cache = Cache(Backend())
        redis_cache.backend = mock_client
        redis_cache.backend.get_cache.return_value = ''

        # Create a function with the decorator
        @redis_cache.cache(invalidator=True)
        def test_function(a, b, c=None, d=None):
            return a

        def cache_key_for(*args, **kwargs):
            return redis_cache._generate_cache_key(test_function, args, kwargs)

        # Call that function
        test_a = 'input'
        test_b = 'b'
        test_c = True
        test_d = False
        function_response, invalidator \
            = test_function(test_a, test_b, c=test_c, d=test_d)

        expected_hash = cache_key_for(test_a, test_b, c=test_c, d=test_d)
        redis_cache.backend.get_cache.assert_called_once_with(expected_hash)
        redis_cache.backend.set_cache_and_expire.assert_called_once_with(
            expected_hash, pickle.dumps(test_a), DEFAULT_EXPIRATION)

        # Call the cache invalidator
        invalidator()
        mock_client.invalidate_key.assert_called_once_with(expected_hash)

    def test_cache_miss_expiration(self):
        """
        Tests a cache miss with an expiration given
        """
        test_param = 'cache hit test'
        ttl = 100
        mock_client = Mock()
        # Simulates a cache hit
        redis_cache = Cache(Backend())
        redis_cache.backend = mock_client
        redis_cache.backend.get_cache.return_value = ''

        # Create a function with the decorator
        @redis_cache.cache(expiration=ttl)
        def test_function(a):
            return a

        def cache_key_for(*args, **kwargs):
            return redis_cache._generate_cache_key(test_function, args, kwargs)

        # Call that function
        function_response = test_function(test_param)
        expected_hash = cache_key_for(test_param)
        redis_cache.backend.get_cache.assert_called_once_with(expected_hash)
        redis_cache.backend.set_cache_and_expire.assert_called_once_with(
            expected_hash, pickle.dumps(test_param), ttl)
        self.assertEqual(redis_cache.backend.set_cache.call_count, 0)

    def test_cache_hit(self):
        """
        Tests a cache hit
        """
        test_param = 'cache hit test'
        mock_client = Mock()
        # Simulates a cache hit
        redis_cache = Cache(Backend())
        redis_cache.backend = mock_client
        redis_cache.backend.get_cache.return_value = pickle.dumps(test_param)

        # Create a function with the decorator
        @redis_cache.cache()
        def test_function(a):
            return a

        def cache_key_for(*args, **kwargs):
            return redis_cache._generate_cache_key(test_function, args, kwargs)

        # Call that function
        function_response = test_function(test_param)
        expected_hash = cache_key_for(test_param)
        redis_cache.backend.get_cache.assert_called_once_with(expected_hash)
        self.assertEqual(redis_cache.backend.set_cache.call_count, 0)
        self.assertEqual(function_response, test_param)

    def test_cache_hit_invalidate(self):
        """
        Tests a cache hit with invalidation
        """
        test_param = 'cache hit test'
        mock_client = Mock()
        # Simulates a cache hit
        redis_cache = Cache(Backend())
        redis_cache.backend = mock_client
        redis_cache.backend.get_cache.return_value = pickle.dumps(test_param)

        # Create a function with the decorator and invalidator param
        @redis_cache.cache(invalidator=True)
        def test_function(a):
            return a

        def cache_key_for(*args, **kwargs):
            return redis_cache._generate_cache_key(test_function, args, kwargs)

        # Call that function
        function_response, invalidator = test_function(test_param)
        expected_hash = cache_key_for(test_param)
        redis_cache.backend.get_cache.assert_called_once_with(expected_hash)
        self.assertEqual(redis_cache.backend.set_cache.call_count, 0)
        self.assertEqual(function_response, test_param)

        # Invalidator should be callable
        self.assertTrue(hasattr(invalidator, '__call__'))

        # Invalidate the cache
        invalidator()
        # Cache entry should have been deleted
        redis_cache.backend.invalidate_key.assert_called_once_with(expected_hash)

    def test_redis_failure(self):
        """
        Tests that the function gets ran as expected when Redis fails
        """
        test_param = 'cache hit test'
        mock_client = Mock()
        # Simulates a cache hit
        redis_cache = Cache(Backend())
        redis_cache.backend = mock_client
        redis_cache.backend.get_cache.side_effect = BackendException

        # Create a function with the decorator
        @redis_cache.cache()
        def test_function(a):
            return a

        def cache_key_for(*args, **kwargs):
            return redis_cache._generate_cache_key(test_function, args, kwargs)

        # Call that function
        function_response = test_function(test_param)
        expected_hash = cache_key_for(test_param)
        redis_cache.backend.get_cache.assert_called_once_with(expected_hash)
        self.assertEqual(redis_cache.backend.set_cache.call_count, 0)
        self.assertEqual(function_response, test_param)

        @redis_cache.cache(invalidator=True)
        def test_function(a):
            return a

        function_response, invalidator = test_function(test_param)
        self.assertIsNone(invalidator)

    def test_cache_custom_signature(self):
        """
        Tests a cache hit with custom signature
        """
        test_param = 'cache hit test'
        mock_client = Mock()
        # Simulates a cache hit
        redis_cache = Cache(Backend())
        redis_cache.backend = mock_client
        redis_cache.backend.get_cache.return_value = pickle.dumps(test_param)

        def test_signature_builder(*args, **kwargs):
            return "test"

        # Create a function with the decorator
        @redis_cache.cache(signature_generator=test_signature_builder)
        def test_function(a):
            return a

        def cache_key_for(*args, **kwargs):
            return redis_cache._generate_cache_key(
                test_function, args, kwargs,
                signature_generator=test_signature_builder)

        # Call that function
        function_response = test_function(test_param)
        expected_hash = cache_key_for(test_param)
        redis_cache.backend.get_cache.assert_called_once_with(expected_hash)
        self.assertEqual(redis_cache.backend.set_cache.call_count, 0)
        self.assertEqual(function_response, test_param)

        # Test that the signature_generator must be callable
        @redis_cache.cache(signature_generator='not callable')
        def test_function_not_callable(a):
            return a

        with self.assertRaises(TypeError):
            test_function_not_callable(test_param)

    def test_simple_object_pickle(self):
        """
        Tests caching of a simple Python object with pickling
        """
        mock_client = Mock()
        # Simulates a cache miss
        redis_cache = Cache(Backend())
        redis_cache.backend = mock_client
        redis_cache.backend.get_cache.return_value = ''

        # Create a function with the decorator
        simple_obj = SimpleObject('test', 42)

        @redis_cache.cache()
        def test_function(a):
            return simple_obj

        def cache_key_for(*args, **kwargs):
            return redis_cache._generate_cache_key(test_function, args, kwargs)

        # Call that function
        test_param = 'input'
        function_response = test_function(test_param)
        self.assertEqual(function_response, simple_obj)

        expected_hash = cache_key_for(test_param)
        redis_cache.backend.get_cache.assert_called_once_with(expected_hash)
        redis_cache.backend.set_cache_and_expire.assert_called_once_with(
            expected_hash, pickle.dumps(simple_obj), DEFAULT_EXPIRATION)

        # Call that function, again, expecting a cache hit
        redis_cache.backend.get_cache.return_value = pickle.dumps(simple_obj)
        function_response = test_function(test_param)
        self.assertEqual(function_response, simple_obj)

    def test_simple_object(self):
        """
        Tests that the cache uses an object's __str__ method to generate
        the signature of an object if available
        """
        mock_client = Mock()
        # Simulates a cache miss
        redis_cache = Cache(Backend())
        redis_cache.backend = mock_client
        redis_cache.backend.get_cache.return_value = ''

        class TestClass(object):
            def __init__(self, parameter):
                self.parameter = parameter

            @redis_cache.cache()
            def cache_this_method(self):
                return self.parameter

            def __str__(self):
                return "<TestClass object: parameter=%s>" % self.parameter

        def cache_key_for(arg):
            fn = TestClass.cache_this_method
            args = [TestClass(arg)]
            return redis_cache._generate_cache_key(fn, args)

        param = 'some_param'
        test_class = TestClass(param)
        test_class.cache_this_method()
        expected_hash = cache_key_for(param)
        redis_cache.backend.get_cache.assert_called_once_with(expected_hash)

    def test_cache_on_class_without_str(self):
        """
        Tests that the cache gets populated when invoking a method that takes a
        primitive type as argument on an object that does not implement a custom
        __str__ method.
        """

        mock_client = Mock()
        redis_cache = Cache(Backend())
        redis_cache.backend = mock_client

        class TestClass(object):
            def __init__(self):
                self.call_count = collections.defaultdict(int)

            @redis_cache.cache()
            def echo(self, parameter):
                self.call_count[parameter] += 1
                return parameter

        primitive_argument = 'cache hit test'
        complex_argument = SimpleObject('test', 42)

        for argument in primitive_argument, complex_argument:
            # on the first call, the cache is empty
            instance = TestClass()
            redis_cache.backend.get_cache.return_value = ''
            instance1_return1 = instance.echo(argument)

            # after the first call, the cache is set, i.e. all the subsequent
            # calls will return the previously computed value from cache
            redis_cache.backend.get_cache.return_value = pickle.dumps(argument)
            instance1_return2 = instance.echo(argument)
            instance1_return3 = instance.echo(argument)
            self.assertEqual(instance1_return1, argument)
            self.assertEqual(instance1_return2, argument)
            self.assertEqual(instance1_return3, argument)
            self.assertEqual(instance.call_count[argument], 1)

            # the cache should also be hit for calls to the same method on a new
            # but equivalent object
            equivalent_instance = TestClass()
            instance2_return1 = equivalent_instance.echo(argument)
            instance2_return2 = equivalent_instance.echo(argument)
            self.assertEqual(instance2_return1, argument)
            self.assertEqual(instance2_return2, argument)
            self.assertEqual(equivalent_instance.call_count[argument], 0)

    def test_cache_on_stateful_class_without_str(self):
        """
        Tests that the cache gets populated when invoking a method on an object
        that is stateful and that doesn't implement a custom __str__ method.

        Some object are stateful, i.e. their methods will return different
        values at different times in the object's life-cycle. When the state of
        the object changes, we need to make sure that the cache doesn't return
        values for the previous state of the object.
        """
        mock_client = Mock()
        redis_cache = Cache(Backend())
        redis_cache.backend = mock_client

        class TestClass(object):
            def __init__(self, state=None):
                self.state = state

            @redis_cache.cache()
            def some_method(self):
                return self.state

        def cache_key_for(state):
            fn = TestClass.some_method
            args = [TestClass(state)]
            return redis_cache._generate_cache_key(fn, args)

        state1 = 'some simple type state'
        state2 = SimpleObject('some complex type state', 123)

        def cache_get(cache_key):
            if cache_key == cache_key_for(state1):
                return pickle.dumps(state1)
            if cache_key == cache_key_for(state2):
                return pickle.dumps(state2)
            raise ValueError('called cache for hash: {}'.format(cache_key))

        redis_cache.backend.get_cache.side_effect = cache_get

        # call the object in some initial state
        stateful_instance = TestClass()
        stateful_instance.state = state1
        return_value_for_state1 = stateful_instance.some_method()

        # mutate the state of the object and make sure that we don't hit the
        # cache for the previous state
        stateful_instance.state = state2
        return_value_for_state2 = stateful_instance.some_method()
        self.assertNotEqual(return_value_for_state1, return_value_for_state2)
