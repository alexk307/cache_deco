from backends.backend_base import Backend
from unittest import TestCase


class BackendTestCase(TestCase):

    def setUp(self):
        self.backend = Backend()

    def test_not_implemented(self):

        with self.assertRaises(NotImplementedError):
            self.backend.get_cache('somekey')

        with self.assertRaises(NotImplementedError):
            self.backend.set_cache('somekey', 'somevalue')

        with self.assertRaises(NotImplementedError):
            self.backend.invalidate_key('somekey')

        with self.assertRaises(NotImplementedError):
            self.backend.set_cache_and_expire('somekey', 'somevalue', 'time')