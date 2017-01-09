""" tests hdfsclient library mkdir"""

import unittest
import hdfsclient
import os


class HDFSClientMkdirTest(unittest.TestCase):

    def setUp(self):
        super(HDFSClientMkdirTest, self).setUp()
        self.temp_dir = "/user/hadoop/qa_data/temp"
        self.child_dir = "/user/hadoop/qa_data/temp/test"
        hdfsclient.mkdir(self.child_dir, create_parent=True)

    def tearDown(self):
        hdfsclient.rm(self.child_dir, recurse=True)
        hdfsclient.mkdir(self.temp_dir)

    def test_mkdir_empty_dir_simple(self):
        """tests mkdir on empty dir no optional params"""
        test_dir_path = self.child_dir + "/testdir"
        hdfsclient.mkdir(test_dir_path)
        ls_res = hdfsclient.ls(self.child_dir, recurse=True)
        folder_paths = self._extract_file_paths_from_ls_res(ls_res)
        expected_res = [self.child_dir, test_dir_path]
        self.assertItemsEqual(folder_paths, expected_res)

    def test_mkdir_create_one_parent_dir(self):
        """tests mkdir with one parent directory"""
        test_dir_path = self.child_dir + "/test/testdir"
        hdfsclient.mkdir(test_dir_path, create_parent=True)
        ls_res = hdfsclient.ls(self.child_dir, recurse=True)
        folder_paths = self._extract_file_paths_from_ls_res(ls_res)
        expected_res = [self.child_dir, test_dir_path, self.child_dir + "/test"]
        self.assertItemsEqual(folder_paths, expected_res)

    def test_mkdir_mult_parent_dirs(self):
        """tests mkdir with mult parent dirs"""
        test_dir_path = self.child_dir + "/test/test/test/testdir"
        hdfsclient.mkdir(test_dir_path, create_parent=True)
        ls_res = hdfsclient.ls(self.child_dir, recurse=True)
        folder_paths = self._extract_file_paths_from_ls_res(ls_res)
        expected_res = [self.child_dir, test_dir_path, self.child_dir + "/test", self.child_dir + "/test/test", self.child_dir + "/test/test/test"]
        self.assertItemsEqual(folder_paths, expected_res)

    @unittest.skip("hdfsclient: does not error when dir path doesn't exist")
    def test_mkdir_dir_does_not_exist(self):
        """tests mkdir without create parent param, dir doesn't exist"""
        test_dir_path = self.child_dir + "/test/testdir"
        with self.assertRaisesRegexp(Exception, "does not exist"):
            hdfsclient.mkdir(test_dir_path)

    def _extract_file_paths_from_ls_res(self, ls_res):
        return [line["path"] for line in ls_res.data]


if __name__ == '__main__':
    unittest.main()
