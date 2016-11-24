import os
import re

root='/opt/insight-agent'


def get_installed_versions():
    result = []
    for version in os.listdir(root):
        if re.match('^v\d+\.\d+\.\d+$', version) is not None:
            installer_name = "agent-{}".format(version)
            installer_path = os.path.join(root, version, installer_name)
            if os.path.isfile(installer_path):
                # strip the v prefix
                result.append(version[1:])

    return result


def get_path_for_version(version):
    directory = "v" + version
    installer_name = "agent-v" + version
    return os.path.join(root, directory, installer_name)


def get_msi_filename(version):
    return "Palette-Insight-v{version}-installer.msi".format(version=version)


def get_path_and_name_for_verison(version):
    return get_msi_filename(version), get_path_for_version(version)
