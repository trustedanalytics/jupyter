from datetime import datetime

from ordereddict import OrderedDict
from snakebite.client import AutoConfigClient
from tabulate import tabulate


class LsObject(object):
    def __init__(self, data):
        self.data = data

    def _get_file_permission_as_str(self, permission_in_octal):
        numeric_to_str = {'7': 'rwx', '6': 'rw-', '5': 'r-x', '4': 'r--', '3': '-wx', '2': '-w-', '1': '--x',
                          '0': '---'}
        permission = oct(permission_in_octal)
        return '%s%s%s' % (numeric_to_str[permission[1]], numeric_to_str[permission[2]], numeric_to_str[permission[3]])

    def _get_formatted_time(self, timestamp):
        return datetime.fromtimestamp(timestamp / 1000).strftime("%Y-%m-%d %H:%M")

    def _get_file_type(self, file_type):
        return '-' if file_type == 'f' else file_type

    def __repr__(self):
        ls_result = []
        for i in self.data:
            ls_file_stat = OrderedDict()
            ls_file_stat['permissions'] = '%s%s' % (
                self._get_file_type(i['file_type']), self._get_file_permission_as_str(i['permission']))
            ls_file_stat['block_replication'] = i['block_replication']
            ls_file_stat['owner'] = i['owner']
            ls_file_stat['group'] = i['group']
            ls_file_stat['size'] = i['length']
            ls_file_stat['last_modification'] = self._get_formatted_time(i['modification_time'])
            ls_file_stat['path'] = i['path']
            ls_result.append(ls_file_stat)

        return tabulate(ls_result, headers="keys")


def ls(hdfs_path, recurse=False, include_toplevel=True, include_children=False):
    """
    Parameters:
    paths (list) : Paths to list
    recurse (boolean) : Recursive listing
    include_toplevel (boolean) : Include the given path in the listing. If the path is a file, include_toplevel is always True.
    include_children (boolean) : Include child nodes in the listing.
    Returns:
    (list) path listings with attributes
    """
    client = AutoConfigClient()

    path_info = list(client.ls([hdfs_path], recurse, include_toplevel, include_children))

    return LsObject(path_info)


def mkdir(hdfs_path, create_parent=False, mode=0755):
    """
    paths (list of strings) : Paths to create
    create_parent (boolean) : Also create the parent directories
    mode (int) : Mode the directory should be created with
    Returns:
    String mkdir result as json
    """
    client = AutoConfigClient()

    return list(client.mkdir([hdfs_path], create_parent, mode))


def rm(hdfs_path, recurse=False, force=False):
    """
    hdfs_path (str or list of strings) : hdfs files to delete
    recurse (boolean) : recursively delete the folder
    force (boolean) : force deletion (non-interactive) 
    Returns:
    String mkdir result as json
    """
    client = AutoConfigClient()

    return list(client.delete([hdfs_path], recurse))


def mv(src, dest, overwrite=False):
    """
    src (str) : Source path on HDFS
    dest (str) : Destination path on HDFS
    overwrite (boolean) : Overwrite dest if exists
    """
    client = AutoConfigClient()

    list(client.rename2(src, dest, overwrite))
