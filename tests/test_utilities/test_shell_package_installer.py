#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys

import click
from cloudshell.rest.exceptions import FeatureUnavailable, ShellNotFoundException

if sys.version_info >= (3, 0):
    from unittest.mock import MagicMock, patch
    from urllib.error import HTTPError
else:
    from mock import MagicMock, patch
    from urllib2 import HTTPError

from pyfakefs import fake_filesystem_unittest

import shellfoundry.utilities.shell_package_installer as spi
from shellfoundry.exceptions import FatalError
from shellfoundry.utilities.shell_package_installer import (
    SHELL_IS_OFFICIAL_FLAG,
    ShellPackageInstaller,
)


def mock_rest_client(update_side_effect, add_side_effect, get_side_effect):
    mock_client = MagicMock()
    mock_client.update_shell = MagicMock(side_effect=update_side_effect)
    mock_client.add_shell = MagicMock(side_effect=add_side_effect)
    mock_client.get_shell.return_value = {SHELL_IS_OFFICIAL_FLAG: get_side_effect}
    return mock_client


def add_shell_error_message(err_msg):
    return "\n" "    {\n" '        "Message" : "' + err_msg + '"\n' "    }\n"


class TestShellPackageInstaller(fake_filesystem_unittest.TestCase):
    def setUp(self):
        self.setUpPyfakefs()

    @patch("shellfoundry.utilities.shell_package_installer.PackagingRestApiClient")
    @patch(
        "shellfoundry.utilities.shell_package_installer.ShellPackage.get_name_from_definition",  # noqa: E501
        new=MagicMock(return_value="NutShell"),
    )
    def test_install_shell_updates_an_existing_shell(self, rest_client_mock):
        # Arrange
        mock_client = MagicMock()
        mock_client.get_shell.return_value = {SHELL_IS_OFFICIAL_FLAG: False}
        rest_client_mock.return_value = mock_client
        installer = ShellPackageInstaller()

        # Act
        with patch("click.echo"):
            installer.install("work/nut-shell")

        # Assert
        self.assertTrue(mock_client.update_shell.called)

    @patch("shellfoundry.utilities.shell_package_installer.PackagingRestApiClient")
    @patch(
        "shellfoundry.utilities.shell_package_installer.ShellPackage.get_name_from_definition",  # noqa: E501
        new=MagicMock(return_value="NutShell"),
    )
    def test_install_shell_adds_a_new_shell_when_shell_does_not_exist(
        self, rest_client_mock
    ):
        # Arrange
        mock_client = MagicMock()
        mock_client.update_shell = MagicMock(side_effect=ShellNotFoundException())
        mock_client.get_shell.return_value = {SHELL_IS_OFFICIAL_FLAG: False}
        rest_client_mock.return_value = mock_client
        installer = ShellPackageInstaller()

        # Act
        with patch("click.echo"):
            installer.install("work/nut-shell")

        # Assert
        self.assertTrue(mock_client.update_shell.called)
        self.assertTrue(mock_client.add_shell.called)

    @patch("shellfoundry.utilities.shell_package_installer.PackagingRestApiClient")
    @patch(
        "shellfoundry.utilities.shell_package_installer.ShellPackage.get_name_from_definition",  # noqa: E501
        new=MagicMock(return_value="NutShell"),
    )
    def test_shell_add_should_not_be_called_when_update_fails(self, rest_client_mock):
        # Arrange
        mock_client = MagicMock()
        mock_client.update_shell = MagicMock(side_effect=Exception())
        mock_client.get_shell.return_value = {SHELL_IS_OFFICIAL_FLAG: False}
        rest_client_mock.return_value = mock_client
        installer = ShellPackageInstaller()

        # noinspection PyBroadException
        try:
            # Act
            with patch("click.echo"):
                installer.install("work/nut-shell")
        except Exception:
            pass

        # Assert
        self.assertTrue(mock_client.update_shell.called)
        self.assertFalse(mock_client.add_shell.called)

    @patch(
        "shellfoundry.utilities.shell_package_installer.PackagingRestApiClient",
        new=MagicMock(side_effect=Exception()),
    )
    @patch(
        "shellfoundry.utilities.shell_package_installer.ShellPackage.get_name_from_definition",  # noqa: E501
        new=MagicMock(return_value="NutShell"),
    )
    def test_fail_to_open_connection_to_cs(self):
        # Arrange
        # doing that for test to run faster with no sleeps between connection failures
        spi.CloudShell_Retry_Interval_Sec = 0
        installer = ShellPackageInstaller()

        with self.assertRaises(FatalError) as context:
            installer.install("work/nut-shell")

        # Assert
        self.assertTrue(
            context.exception.message
            == "Connection to CloudShell Server failed. Please make sure it is up and running properly."  # noqa: E501
        )

    @patch(
        "shellfoundry.utilities.shell_package_installer.PackagingRestApiClient",
        new=MagicMock(side_effect=HTTPError("", 401, "", None, None)),
    )
    @patch(
        "shellfoundry.utilities.shell_package_installer.ShellPackage.get_name_from_definition",  # noqa: E501
        new=MagicMock(return_value="NutShell"),
    )
    def test_fail_to_login_into_cs(self):
        # Arrange
        # doing that for test to run faster with no sleeps between connection failures
        spi.CloudShell_Retry_Interval_Sec = 0
        installer = ShellPackageInstaller()

        with self.assertRaises(FatalError) as context:
            installer.install("work/nut-shell")

        # Assert
        self.assertTrue(
            context.exception.message
            == u"Login to CloudShell failed. Please verify the credentials in the config"  # noqa: E501
        )

    @patch(
        "shellfoundry.utilities.shell_package_installer.PackagingRestApiClient",
        new=MagicMock(side_effect=HTTPError("", 403, "", None, None)),
    )
    @patch(
        "shellfoundry.utilities.shell_package_installer.ShellPackage.get_name_from_definition",  # noqa: E501
        new=MagicMock(return_value="NutShell"),
    )
    def test_fail_with_http_error_other_than_authentication_error(self):
        # Arrange
        # doing that for test to run faster with no sleeps between connection failures
        spi.CloudShell_Retry_Interval_Sec = 0
        installer = ShellPackageInstaller()

        with self.assertRaises(FatalError) as context:
            installer.install("work/nut-shell")

        # Assert
        self.assertTrue(
            context.exception.message
            == "Connection to CloudShell Server failed. Please make sure it is up and running properly."  # noqa: E501
        )

    @patch(
        "shellfoundry.utilities.shell_package_installer.PackagingRestApiClient",
        new=MagicMock(
            return_value=mock_rest_client(
                update_side_effect=ShellNotFoundException(),
                add_side_effect=Exception(
                    add_shell_error_message("Failed to add shell")
                ),
                get_side_effect=False,
            )
        ),
    )
    def test_fail_to_update_and_than_add_shell(self):
        # Arrange
        self.fs.create_file(
            "work/nut-shell/TOSCA-Metadata/TOSCA.meta",
            contents="TOSCA-Meta-File-Version: 1.0\n"
            "CSAR-Version: 0.1.0\n"
            "Created-By: Anonymous\n"
            "Entry-Definitions: shell-definition.yaml",
        )
        self.fs.create_file(
            "work/nut-shell/shell-definition.yaml",
            contents="tosca_definitions_version: tosca_simple_yaml_1_0\n"
            "metadata:\n"
            "  template_name: NutShell\n"
            "  template_author: Anonymous\n"
            "  template_version: 1.0.0\n"
            "node_types:\n"
            "  vendor.switch.NXOS:\n"
            "    derived_from: cloudshell.nodes.Switch\n"
            "    artifacts:\n"
            "      icon:\n"
            "        file: nxos.png\n"
            "        type: tosca.artifacts.File\n"
            "      driver:\n"
            "        file: NutShellDriver.zip\n"
            "        type: tosca.artifacts.File",
        )
        # doing that for test to run faster with no sleeps between connection failures
        spi.Default_Time_Wait = 0
        installer = ShellPackageInstaller()

        # Act
        with self.assertRaises(FatalError) as context:
            installer.install("work/nut-shell")

        # Assert
        self.assertTrue(
            context.exception.message
            == "Failed to add new shell. CloudShell responded with: 'Failed to add shell'"  # noqa: E501
        )

    @patch("shellfoundry.utilities.shell_package_installer.PackagingRestApiClient")
    @patch(
        "shellfoundry.utilities.shell_package_installer.click.confirm", new=MagicMock()
    )
    @patch(
        "shellfoundry.utilities.shell_package_installer.ShellPackage.get_name_from_definition",  # noqa: E501
        new=MagicMock(return_value="NutShell"),
    )
    def test_install_shell_updates_official_shell_confirm(self, rest_client_mock):
        # Arrange
        mock_client = MagicMock()
        mock_client.get_shell.return_value = {SHELL_IS_OFFICIAL_FLAG: True}
        rest_client_mock.return_value = mock_client
        installer = ShellPackageInstaller()

        # Act
        with patch("click.echo"):
            installer.install("work/nut-shell")

        # Assert
        self.assertTrue(mock_client.update_shell.called)

    @patch("shellfoundry.utilities.shell_package_installer.PackagingRestApiClient")
    @patch(
        "shellfoundry.utilities.shell_package_installer.click.confirm",
        new=MagicMock(side_effect=(click.Abort)),
    )
    @patch(
        "shellfoundry.utilities.shell_package_installer.ShellPackage.get_name_from_definition",  # noqa: E501
        new=MagicMock(return_value="NutShell"),
    )
    def test_install_shell_updates_official_shell_abort(self, rest_client_mock):
        # Arrange
        mock_client = MagicMock()
        mock_client.get_shell.return_value = {SHELL_IS_OFFICIAL_FLAG: True}
        rest_client_mock.return_value = mock_client
        installer = ShellPackageInstaller()

        # Act
        with self.assertRaises(click.Abort):
            installer.install("work/nut-shell")

    @patch("shellfoundry.utilities.shell_package_installer.PackagingRestApiClient")
    @patch(
        "shellfoundry.utilities.shell_package_installer.click.confirm",
        new=MagicMock(side_effect=(FeatureUnavailable)),
    )
    @patch(
        "shellfoundry.utilities.shell_package_installer.ShellPackage.get_name_from_definition",  # noqa: E501
        new=MagicMock(return_value="NutShell"),
    )
    def test_install_shell_updates_official_shell_feature_unavailable(
        self, rest_client_mock
    ):
        # Arrange
        mock_client = MagicMock()
        mock_client.get_shell.return_value = {SHELL_IS_OFFICIAL_FLAG: True}
        rest_client_mock.return_value = mock_client
        installer = ShellPackageInstaller()

        # Act
        with patch("click.echo"):
            installer.install("work/nut-shell")

        # Assert
        self.assertTrue(mock_client.update_shell.called)

    @patch("shellfoundry.utilities.shell_package_installer.PackagingRestApiClient")
    @patch(
        "shellfoundry.utilities.shell_package_installer.click.confirm",
        new=MagicMock(side_effect=(ShellNotFoundException)),
    )
    @patch(
        "shellfoundry.utilities.shell_package_installer.ShellPackage.get_name_from_definition",  # noqa: E501
        new=MagicMock(return_value="NutShell"),
    )
    def test_install_shell_updates_official_shell_not_found(self, rest_client_mock):
        # Arrange
        mock_client = MagicMock()
        mock_client.get_shell.return_value = {SHELL_IS_OFFICIAL_FLAG: True}
        rest_client_mock.return_value = mock_client
        installer = ShellPackageInstaller()

        # Act
        with patch("click.echo"):
            installer.install("work/nut-shell")

        # Assert
        self.assertTrue(mock_client.update_shell.called)
