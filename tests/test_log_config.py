import unittest
from unittest.mock import patch

from mylogger.setlogger import configure_logger


class LoggerConfigurationTests(unittest.TestCase):
    @patch("mylogger.setlogger.setup_logging")
    def test_compatibility_configurer_uses_shared_setup(self, setup_logging):
        configure_logger()

        setup_logging.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
