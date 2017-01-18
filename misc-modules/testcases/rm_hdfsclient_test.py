""" tests hdfsclient library rm"""

import unittest
import hdfsclient
import ntpath


class HDFSClientRmTest(unittest.TestCase):

    def setUp(self):
        super(HDFSClientRmTest, self).setUp()
        self.temp_dir = "/user/hadoop/qa_data/temp"
        self.child_dir = "/user/hadoop/qa_data/temp/test"
        # record the current contents for later comparison
        ls_res = hdfsclient.ls(self.temp_dir, include_toplevel=False, recurse=True)
        self.temp_dir_file_paths = self._extract_file_paths_from_ls_res(ls_res)
        hdfsclient.mkdir(self.child_dir)

    def tearDown(self):
        ls_res = hdfsclient.ls(self.temp_dir, include_toplevel=False, recurse=True)
        file_paths_list = self._extract_file_paths_from_ls_res(ls_res)
        if self.child_dir in file_paths_list:
            hdfsclient.rm(self.child_dir, recurse=True)

    def test_rm_file_simple(self):
        """tests rm file"""
        item_to_remove = self.temp_dir_file_paths[0]
        hdfsclient.rm(item_to_remove)
        self.temp_dir_file_paths.remove(item_to_remove)
        ls_res = hdfsclient.ls(self.temp_dir, recurse=True)
        file_paths_list = self._extract_file_paths_from_ls_res(ls_res)
        expected_res = [self.temp_dir, self.child_dir] + self.temp_dir_file_paths
        self.assertItemsEqual(file_paths_list, expected_res)

    @unittest.skip("hdfsclient: force param for rm does nothing")
    def test_rm_file_force_true(self):
        """tests rm a file w force=True"""
        item_to_remove = self.temp_dir_file_paths[0]
        hdfsclient.rm(item_to_remove, force=False)
        self.temp_dir_file_paths.remove(item_to_remove)
        ls_res = hdfsclient.ls(self.temp_dir, recurse=True)
        actual_res = self._extract_file_paths_from_ls_res(ls_res)
        expected_res = [self.temp_dir, self.child_dir] + self.temp_dir_file_paths
        self.assertItemsEqual(expected_res, actual_res)

    def test_rm_file_recurse_true(self):
        """test rm file w recurse=True"""
        item_to_remove = self.temp_dir_file_paths[0]
        hdfsclient.rm(item_to_remove, recurse=True)
        self.temp_dir_file_paths.remove(item_to_remove)
        ls_res = hdfsclient.ls(self.temp_dir, recurse=True)
        actual_res = self._extract_file_paths_from_ls_res(ls_res)
        expected_res = [self.temp_dir, self.child_dir] + self.temp_dir_file_paths
        self.assertItemsEqual(expected_res, actual_res)

    def test_rm_empty_directory(self):
        """tests rm on empty dir"""
        with self.assertRaisesRegexp(Exception, "Is a directory"):
            hdfsclient.rm(self.child_dir)

    def test_rm_empty_dir_force_true(self):
        """tests rm on empty dir with force=True"""
        with self.assertRaisesRegexp(Exception, "Is a directory"):
            hdfsclient.rm(self.child_dir)

    def test_rm_empty_dir_recursive(self):
        """tests rm on empty dir recurse=True"""
        hdfsclient.rm(self.child_dir, recurse=True)
        ls_res = hdfsclient.ls(self.temp_dir, recurse=True)
        actual_res = self._extract_file_paths_from_ls_res(ls_res)
        expected_res = [self.temp_dir] + self.temp_dir_file_paths
        self.assertItemsEqual(actual_res, expected_res)

    def test_rm_nested_dir_recursive(self):
        """tests rm on nested dir recurse=True"""
        # first we initialize the dir we want to rm
        hdfsclient.mkdir(self.child_dir + "/innerdir/innerdir/innerdir", create_parent=True)
        ls_res = hdfsclient.ls(self.child_dir, recurse=True)
        file_paths = self._extract_file_paths_from_ls_res(ls_res)
        # here we are making sure it is properly initialized
        expected_res = [self.child_dir, self.child_dir + "/innerdir", self.child_dir + "/innerdir/innerdir",
                        self.child_dir + "/innerdir/innerdir/innerdir"]
        self.assertItemsEqual(file_paths, expected_res)
        # now we remove it
        hdfsclient.rm(self.child_dir, recurse=True)
        ls_res = hdfsclient.ls(self.temp_dir, recurse=True)
        # and ensure it is in fact removed
        actual_res = self._extract_file_paths_from_ls_res(ls_res)
        expected_res = [self.temp_dir] + self.temp_dir_file_paths
        self.assertItemsEqual(actual_res, expected_res)

    @unittest.skip("hdfsclient: force param for rm does nothing")
    def test_rm_nested_dir_recursive_force_true(self):
        """tests rm on nested dir recurse=True and force=True"""
        hdfsclient.mkdir(self.child_dir + "/innerdir/innerdir/innerdir", create_parent=True)
        ls_res = hdfsclient.ls(self.child_dir, recurse=True)
        file_paths = self._extract_file_paths_from_ls_res(ls_res)
        expected_res = [self.child_dir, self.child_dir + "/innerdir", self.child_dir + "/innerdir/innerdir",
                        self.child_dir + "/innerdir/innerdir/innerdir"]
        self.assertItemsEqual(file_paths, expected_res)
        hdfsclient.rm(self.child_dir, recurse=True, force=True)
        ls_res = hdfsclient.ls(self.temp_dir, recurse=True)
        actual_res = self._extract_file_paths_from_ls_res(ls_res)
        expected_res = [self.temp_dir] + self.temp_dir_file_paths
        self.assertItemsEqual(actual_res, expected_res)

    def test_rm_dir_with_files(self):
        """test rm dir with files recurse=True"""
        # first we initalize a nested dir to test on
        hdfsclient.mkdir(self.child_dir + "/innerdir", create_parent=True)
        ls_res = hdfsclient.ls(self.temp_dir, recurse=True, include_toplevel=False)
        file_names = self._extract_file_names_from_ls_res(ls_res)
        moved_items = []
        # we move a couple items into the folder
        for x in range(0, 2):
            item_to_move = file_names[x]
            hdfsclient.mv(self.temp_dir + "/" + str(item_to_move), self.child_dir + "/innerdir/" + str(item_to_move))
            moved_items.append(item_to_move)
            self.temp_dir_file_paths.remove(self.temp_dir + "/" + str(item_to_move))
        # now we remove the folder and its contents
        hdfsclient.rm(self.child_dir, recurse=True)
        # finally we ensure it has been properly removed
        ls_res = hdfsclient.ls(self.temp_dir, recurse=True)
        actual_res = self._extract_file_paths_from_ls_res(ls_res)
        expected_res = [self.temp_dir] + self.temp_dir_file_paths
        self.assertItemsEqual(expected_res, actual_res)

    def _extract_file_paths_from_ls_res(self, ls_res):
        return [line["path"] for line in ls_res.data]

    def _extract_file_names_from_ls_res(self, ls_res):
        file_paths = [line["path"] for line in ls_res.data]
        return [ntpath.basename(line) for line in file_paths if ".txt" in line]


if __name__ == '__main__':
    unittest.main()
