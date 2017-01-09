""" tests hdfsclient library"""

import unittest
import hdfsclient
import os


class HDFSClientMvTest(unittest.TestCase):

    def setUp(self):
        super(HDFSClientMvTest, self).setUp()
        self.temp_dir = "/user/hadoop/qa_data/temp"
        self.child_dir = "/user/hadoop/qa_data/temp/test"
        self.moved_dir = "/user/hadoop/qa_data/temp/test2"
        ls_res = hdfsclient.ls(self.temp_dir, include_toplevel=False, recurse=True)
        self.temp_dir_file_paths = self._extract_file_paths_from_ls_res(ls_res)
        hdfsclient.mkdir(self.child_dir)

    def tearDown(self):
        ls_res = hdfsclient.ls(self.temp_dir, recurse=True)
        ls_res_paths = self._extract_file_paths_from_ls_res(ls_res)
        if self.child_dir in ls_res_paths:
            hdfsclient.rm(self.child_dir, recurse=True)
        if self.moved_dir in ls_res_paths:
            hdfsclient.rm(self.moved_dir, recurse=True)

    def test_mv_dir_simple(self):
        """tests mv dir simple"""
        hdfsclient.mv(self.child_dir, self.moved_dir)
        ls_res = hdfsclient.ls(self.temp_dir, recurse=True)
        actual_res = self._extract_file_paths_from_ls_res(ls_res)
        expected_res = [self.temp_dir, self.moved_dir] + self.temp_dir_file_paths
        self.assertItemsEqual(actual_res, expected_res)

    def test_mv_dir_nested(self):
        """tests mv dir nested directory"""
        hdfsclient.mkdir(self.child_dir + "/innerdir/innerdir", create_parent=True)
        ls_res = hdfsclient.ls(self.temp_dir, recurse=True)
        actual_res = self._extract_file_paths_from_ls_res(ls_res)
        expected_res = [self.temp_dir, self.child_dir, self.child_dir + "/innerdir", self.child_dir + "/innerdir/innerdir"] + self.temp_dir_file_paths
        self.assertItemsEqual(actual_res, expected_res)

    def test_mv_dir_dest_and_src_same(self):
        """tests mv dir with src and dest the same"""
        with self.assertRaisesRegexp(Exception, "The source " + str(self.child_dir) + " and destination " + str(self.child_dir) + " are the same"):
            hdfsclient.mv(self.child_dir, self.child_dir)

    def test_mv_dir_overwrite_is_false_dir_already_exists(self):
        """test mv dir with dest already exist, no overwrite"""
        hdfsclient.mkdir(self.moved_dir)
        with self.assertRaisesRegexp(Exception, "rename destination " + str(self.moved_dir) + " already exists"):
            hdfsclient.mv(self.child_dir, self.moved_dir)

    def test_mv_dir_overwrite_empty_dest_and_empty_src(self):
        """tets mv dir with dest and src empty, overwrite"""
        hdfsclient.mkdir(self.moved_dir)
        hdfsclient.mv(self.child_dir, self.moved_dir, overwrite=True)
        ls_res = hdfsclient.ls(self.temp_dir, recurse=True)
        actual_res = self._extract_file_paths_from_ls_res(ls_res)
        expected_res = [self.temp_dir, self.moved_dir] + self.temp_dir_file_paths
        self.assertItemsEqual(expected_res, actual_res)

    def test_mv_overwrite_dir_nonempty_dest(self):
        """test mv dir with overwrite=true non-empty dest"""
        hdfsclient.mkdir(self.moved_dir + "/innerdir", create_parent=True)
        with self.assertRaisesRegexp(Exception, "destination directory is not empty"):
            hdfsclient.mv(self.child_dir, self.moved_dir, overwrite=True)

    def test_mv_overwrite_dir_nonempty_src_nonempty_dest(self):
        """tests mv dir w overwrite=True non-empty dest and src"""
        hdfsclient.mkdir(self.moved_dir + "/innerdir2", create_parent=True)
        hdfsclient.mkdir(self.child_dir + "/innerdir", create_parent=True)
        with self.assertRaisesRegexp(Exception, "destination directory is not empty"):
            hdfsclient.mv(self.child_dir, self.moved_dir, overwrite=True)

    def test_mv_overwrite_dir_nonempty_src_empty_dest(self):
        """tests mv dir w overwrite=True non-empty src but dest is empty"""
        hdfsclient.mkdir(self.child_dir + "/innerdir", create_parent=True)
        hdfsclient.mkdir(self.moved_dir, create_parent=True)
        hdfsclient.mv(self.child_dir, self.moved_dir, overwrite=True)
        ls_res = hdfsclient.ls(self.temp_dir, recurse=True)
        actual_res = self._extract_file_paths_from_ls_res(ls_res)
        expected_res = [self.moved_dir, self.moved_dir + "/innerdir", self.temp_dir] + self.temp_dir_file_paths
        self.assertItemsEqual(expected_res, actual_res)

    def test_mv_overwrite_dest_DNE_emtpy_src(self):
        """tests mv dir w overwrite=True empty src dest does not exist"""
        hdfsclient.mv(self.child_dir, self.moved_dir, overwrite=True)
        ls_res = hdfsclient.ls(self.temp_dir, recurse=True)
        actual_res = self._extract_file_paths_from_ls_res(ls_res)
        expected_res = [self.temp_dir, self.moved_dir] + self.temp_dir_file_paths
        self.assertItemsEqual(expected_res, actual_res)

    def test_mv_overwrite_dest_DNE_nonempty_src(self):
        """tests mv dir w overwrite=True nonempty src dest does not exist"""
        hdfsclient.mkdir(self.child_dir + "/innerdir", create_parent=True)
        hdfsclient.mv(self.child_dir, self.moved_dir, overwrite=True)
        ls_res = hdfsclient.ls(self.temp_dir, recurse=True)
        actual_res = self._extract_file_paths_from_ls_res(ls_res)
        expected_res = [self.temp_dir, self.moved_dir, self.moved_dir + "/innerdir"] + self.temp_dir_file_paths
        self.assertItemsEqual(expected_res, actual_res)

    @unittest.skip("hdfsclient: doesn't allow moving files")
    def test_mv_one_file_simple(self):
        """tests mv one file"""
        hdfsclient.mv(self.temp_dir_file_paths[0], self.child_dir)
        ls_res = hdfsclient.ls(self.child_dir)
        file_paths_list = self._extract_file_paths_from_ls_res(ls_res)
        expected_res = [self.child_dir, self.child_dir + "testfile1.txt"]
        self.assertItemsEqual(file_paths_list, expected_res)

    @unittest.skip("hdfsclient: doesn't allow moving files")
    def test_mv_one_file_overwrite_true_dest_file_DNE(self):
        """tests mv one file w overwrite=True dest file does not exist"""
        hdfsclient.mv(self.temp_dir_file_paths[0], self.child_dir, overwrite=True)
        ls_res = hdfsclient.ls(self.child_dir)
        file_paths_list = self._extract_file_paths_from_ls_res(ls_res)
        expected_res = [self.child_dir, self.child_dir + "testfile1.txt"]
        self.assertItemsEqual(file_paths_list, expected_res)

    @unittest.skip("hdfsclient: doesn't allow moving files")
    def test_mv_one_file_overwrite_false_dest_already_exists(self):
        """tests mv one file w overwrite=False dest already exists"""
        with self.assertRaisesRegexp(Exception, "already exists"):
            hdfsclient.mv(self.temp_dir_file_paths[0], self.temp_dir_file_paths[1])

    @unittest.skip("hdfsclient: doesn't allow moving files")
    def test_mv_one_file_overwrite_true_dest_file_exists(self):
        """tests mv one file w overwrite=True dest file exists"""
        hdfsclient.mv(self.temp_dir_file_paths[0], self.temp_dir_file_paths[1], overwrite=True)
        self.temp_dir_file_paths.remove(self.temp_dir_file_paths[1])
        ls_res = hdfsclient.ls(self.child_dir)
        file_paths_list = self._extract_file_paths_from_ls_res(ls_res)
        expected_res = [self.child_dir, self.temp_dir] + self.temp_dir_file_paths 
        self.assertItemsEqual(file_paths_list, expected_res)

    def test_mv_file_does_not_exist(self):
        """tests mv file that doesn't exist"""
        with self.assertRaisesRegexp(Exception, "No such file or directory"):
            hdfsclient.mv(self.temp_dir + "/doesntexist.txt", self.moved_dir)

    def _extract_file_paths_from_ls_res(self, ls_res):
        return [line["path"] for line in ls_res.data]


if __name__ == '__main__':
    unittest.main()
