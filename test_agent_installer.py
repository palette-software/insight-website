import os
from unittest import TestCase
from unittest.mock import patch
from assertpy import assert_that
import agent_installer


class TestAgentInstaller(TestCase):
    def setUp(self):
        self.directories = ["v2.0.1", "2.0.2", "v2.0.14", "alma"]

    @patch("os.listdir")
    @patch('os.path.isfile')
    def test_get_installed_versions_no_installer_files(self, mock_isfile, mock_listdir):
        mock_listdir.return_value = self.directories
        mock_isfile.return_value = False
        assert_that(agent_installer.get_installed_versions()).is_equal_to([])

    @patch("os.listdir")
    @patch('os.path.isfile')
    def test_get_installed_versions_one_installer(self, mock_isfile, mock_listdir):
        mock_listdir.return_value = self.directories

        def v2_0_14_exits(path):
            return path == os.path.join(agent_installer.root, 'v2.0.14', 'agent-v2.0.14')

        mock_isfile.side_effect = v2_0_14_exits
        assert_that(agent_installer.get_installed_versions()).is_equal_to(["2.0.14"])

    def test_get_path_for_version(self):
        expected_result = os.path.join(agent_installer.root, 'v2.1.1', 'agent-v2.1.1')
        assert_that(agent_installer.get_path_for_version('2.1.1')).is_equal_to(expected_result)

    def test_get_msi_filename(self):
        assert_that(agent_installer.get_msi_filename('11.1.111')).is_equal_to('Palette-Insight-v11.1.111-installer.msi')
