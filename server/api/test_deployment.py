import os
import unittest
from unittest.mock import patch

from api.deployment import required_environment


class RequiredEnvironmentTests(unittest.TestCase):
    def test_rejects_a_missing_required_setting(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "API_SECRET_KEY"):
                required_environment("API_SECRET_KEY")

    def test_returns_a_configured_required_setting(self):
        with patch.dict(os.environ, {"API_SECRET_KEY": "configured-secret"}, clear=True):
            self.assertEqual(required_environment("API_SECRET_KEY"), "configured-secret")
