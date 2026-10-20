import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('deployment', Path(__file__).with_name('deploy.py'))
deployment = importlib.util.module_from_spec(spec)
spec.loader.exec_module(deployment)


class DeploymentGuards(unittest.TestCase):
    def test_rejects_unpinned_image_before_any_operation(self):
        with patch.object(sys, 'argv', ['deploy.py', 'latest', 'a'*40]), patch.object(deployment, 'command') as command:
            with self.assertRaises(ValueError): deployment.main()
            command.assert_not_called()

    def test_rejects_wrong_engine_before_inspecting_or_stopping_app(self):
        with patch.object(sys, 'argv', ['deploy.py', 'local/jellyfin-homelab:'+'a'*40, 'a'*40]), patch.object(deployment, 'command', return_value='desktop-linux\n') as command:
            with self.assertRaises(ValueError): deployment.main()
            self.assertEqual(1, command.call_count)

    def test_rejects_image_revision_mismatch(self):
        with patch.object(sys, 'argv', ['deploy.py', 'local/jellyfin-homelab:'+'a'*40, 'a'*40]), patch.object(deployment, 'command', side_effect=['docker\n', 'b'*40]) as command:
            with self.assertRaises(ValueError): deployment.main()
            self.assertEqual(2, command.call_count)


if __name__ == '__main__': unittest.main()
