""" tests hdfsclient library"""

import unittest
import hdfsclient


class HDFSClientTest(unittest.TestCase):

    def setUp(self):
        super(HDFSClientTest, self).setUp()
        self.temp_dir = "/user/hadoop/qa_data/temp"
        self.child_dir = "/user/hadoop/qa_data/temp/test"
        # record the initial contents of the temp folder for later comparison
        ls_res = hdfsclient.ls(self.temp_dir, include_toplevel=False, recurse=True)
        self.temp_dir_file_paths = self._extract_file_paths_from_ls_res(ls_res)
        # initialize a subdirectory in our temp test directory
        hdfsclient.mkdir(self.child_dir)

    def tearDown(self):
        hdfsclient.rm(self.child_dir, recurse=True)

    def test_ls_empty_dir_simple(self):
        """tests ls on empty dir no params"""
        ls_res = hdfsclient.ls(self.child_dir)
        file_paths_list = self._extract_file_paths_from_ls_res(ls_res)
        self.assertItemsEqual(file_paths_list, [self.child_dir])

    def test_ls_empty_dir_recursive(self):
        """test ls on empty dir with recursive=True"""
        ls_res = hdfsclient.ls(self.child_dir, recurse=True)
        file_paths_list = self._extract_file_paths_from_ls_res(ls_res)
        self.assertItemsEqual(file_paths_list, [self.child_dir])

    def test_ls_empty_dir_include_top_level(self):
        """tests ls on empty dir including top lvl"""
        ls_res = hdfsclient.ls(self.child_dir, include_toplevel=True)
        file_paths_list = self._extract_file_paths_from_ls_res(ls_res)
        self.assertItemsEqual(file_paths_list, [self.child_dir])

    def test_ls_empty_dir_exclude_top_level(self):
        """tests ls on empty dir excluding top lvl"""
        ls_res = hdfsclient.ls(self.child_dir, include_toplevel=False)
        file_paths_list = [line["path"] for line in ls_res.data]
        self.assertItemsEqual(file_paths_list, [])

    def test_ls_empty_dir_include_children(self):
        """tests ls on empty dir including children"""
        ls_res = hdfsclient.ls(self.child_dir, include_children=True)
        file_paths_list = self._extract_file_paths_from_ls_res(ls_res)
        self.assertItemsEqual(file_paths_list, [self.child_dir])

    def test_ls_empty_dir_exclude_children(self):
        """tests ls on empty dir excluding children"""
        ls_res = hdfsclient.ls(self.child_dir, include_children=False)
        file_paths_list = self._extract_file_paths_from_ls_res(ls_res)
        self.assertItemsEqual(file_paths_list, [self.child_dir])

    def test_ls_with_test_files_simple(self):
        """tests ls with dummy files"""
        ls_res = hdfsclient.ls(self.temp_dir)
        file_paths_list = self._extract_file_paths_from_ls_res(ls_res)
        self.assertItemsEqual(file_paths_list, [self.temp_dir])

    def test_ls_with_test_files_recursive(self):
        """tests ls with dummy files recursive"""
        ls_res = hdfsclient.ls(self.temp_dir, recurse=True)
        file_paths_list = self._extract_file_paths_from_ls_res(ls_res)
        expected_res = [self.temp_dir, self.child_dir] + self.temp_dir_file_paths
        self.assertItemsEqual(file_paths_list, expected_res)

    def test_ls_with_test_files_recursive_exclude_toplevel(self):
        """tests ls with dummy files recursive exclude toplvl"""
        ls_res = hdfsclient.ls(self.temp_dir, recurse=True, include_toplevel=False)
        file_paths_list = self._extract_file_paths_from_ls_res(ls_res)
        expected_res = [self.child_dir] + self.temp_dir_file_paths
        self.assertItemsEqual(file_paths_list, expected_res)

    def test_ls_with_test_files_including_top_level(self):
        """tests ls with dummy files top level included"""
        ls_res = hdfsclient.ls(self.temp_dir, include_toplevel=True)
        file_paths_list = self._extract_file_paths_from_ls_res(ls_res)
        self.assertItemsEqual(file_paths_list, [self.temp_dir])

    def test_ls_with_test_files_include_children(self):
        """tests ls with dummy files children included"""
        ls_res = hdfsclient.ls(self.temp_dir, include_children=True)
        file_paths_list = self._extract_file_paths_from_ls_res(ls_res)
        expected_res = [self.child_dir, self.temp_dir] + self.temp_dir_file_paths
        self.assertItemsEqual(file_paths_list, expected_res)

    def test_ls_with_test_files_include_children_exclude_toplevel(self):
        """tests ls with dummy files children included toplvl excluded"""
        ls_res = hdfsclient.ls(self.temp_dir, include_children=True, include_toplevel=False)
        file_paths_list = self._extract_file_paths_from_ls_res(ls_res)
        expected_res = [self.child_dir] + self.temp_dir_file_paths
        self.assertItemsEqual(file_paths_list, expected_res)

    def test_ls_with_test_files_excluding_top_level(self):
        """tests ls with dummy files top level excluded"""
        ls_res = hdfsclient.ls(self.temp_dir, include_toplevel=False)
        file_paths_list = self._extract_file_paths_from_ls_res(ls_res)
        self.assertItemsEqual(file_paths_list, [])

    def test_ls_with_test_files_recursive_include_children(self):
        """tests ls with dummy files recursive include children"""
        ls_res = hdfsclient.ls(self.temp_dir, include_children=True, recurse=True)
        file_paths_list = self._extract_file_paths_from_ls_res(ls_res)
        expected_res = self.temp_dir_file_paths + [self.temp_dir, self.child_dir]
        self.assertItemsEqual(file_paths_list, expected_res)

    def test_ls_with_test_files_recursive_include_children_exclude_toplvl(self):
        """tests ls with dumm files recursive include children exclude toplvl"""
        ls_res = hdfsclient.ls(self.temp_dir, recurse=True, include_children=True, include_toplevel=False)
        file_paths_list = self._extract_file_paths_from_ls_res(ls_res)
        expected_res = self.temp_dir_file_paths + [self.child_dir]
        self.assertItemsEqual(file_paths_list, expected_res)

    def _extract_file_paths_from_ls_res(self, ls_res):
        """given an ls res object, return file paths"""
        return [line["path"] for line in ls_res.data]


if __name__ == '__main__':
    unittest.main()
