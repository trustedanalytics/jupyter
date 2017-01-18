import errno
import json
import os
import subprocess
import time

from concurrent.futures import ProcessPoolExecutor as Pool
from notebook.base.handlers import IPythonHandler

STATUS_FILE = 'STATUS.log'
LOG_FILE = 'LOG.log'

APP_STATUS = {
    'UPLOADED': 'uploaded',
    'SUBMITTED': 'submitted',
    'COMPLETED': 'completed'
}

APP_SETTINGS = {
    'TEMPLATE_PATH': r"templates",
    'STATIC_PATH': r"templates/static",
    'UPLOADS_PATH': r"uploads",
    "XSRF_COOKIES": False
}

RESPONSE = {
    "DRIVER_PATH": 'driver-path',  # submitted app id
    "APP_STATUS": 'app-status',  # UPLOADED, SUBMITTED, COMPLETED
    "APP_DIR": 'app-dir',  # Path where the app bits are uploaded
    "LAST_UPDATED": "last-updated"  # The time and date of last status update
}


def update_status(driver_path, app_status=APP_STATUS['COMPLETED']):
    """
    :param driver_path: path to the main sparktk/pyspark script in the uploads directory
    :param app_status: final status of the app after this update written to STATUS_FILE
    :return: handler to the updated STATUS_FILE
    """
    app_dir = os.path.dirname(driver_path)
    status_file = open(os.path.dirname(driver_path) + '/' + STATUS_FILE, 'a+w')
    status_file.write('\n')
    status_file.write(json.dumps(
        dict(
            {
                RESPONSE['DRIVER_PATH']: driver_path,
                RESPONSE['APP_STATUS']: app_status,
                RESPONSE['APP_DIR']: app_dir,
                RESPONSE['LAST_UPDATED']: time.strftime("%c")
            }
        )
    ))
    status_file.close()
    return status_file


class IndexHandler(IPythonHandler):
    """
    implements the "hello" REST api endpoint.

    Examples:
        curl http://<JUPYTER_NOTEBOOK_URL>/hello
    """

    def get(self):
        self.write("Hello From Jupyter")

    def write_error(self, status_code, **kwargs):
        self.write("Gosh darnit, user! You caused a %d error." % status_code)


class UploadFormHandler(IPythonHandler):
    def get(self):
        self.render("templates/fileuploadform.html")


class UploadHandler(IPythonHandler):
    """
    implements the "upload" REST api endpoint.
    currently the only way to upload files to Jupyter is using the upload Form.
    after each attemp to upload the file(s) are loaded into a directory format like "uploads/dddd" where d is a digit.

    Examples:
        curl http://<JUPYTER_NOTEBOOK_URL>/upload -F "filearg=@/home/ashahba/frame-basics.py"
    """

    def create_upload_dir(self):
        """
        :return: name of the directory created that contains uploaded script(s), jars
        """
        max_dir_len = len('0000')
        i = 0
        dir_name = APP_SETTINGS['UPLOADS_PATH'] + '/%s' % str(i).zfill(max_dir_len)
        while os.path.exists(dir_name) and (i < 10 ** max_dir_len):
            i += 1
            dir_name = APP_SETTINGS['UPLOADS_PATH'] + '/%s' % str(i).zfill(max_dir_len)

        if (i >= 10 ** max_dir_len):
            raise Exception("Too many uploads have been done!\nPlease run some cleanup before uploading more files.\n")

        try:
            os.makedirs(dir_name)
        except OSError as exc:
            if exc.errno == errno.EEXIST and os.path.isdir(dir_name):
                pass
            else:
                raise Exception("Directory creation failed.\n")

        return dir_name

    def post(self):
        app_dir = self.create_upload_dir()
        for filearg in self.request.files['filearg']:
            original_fname = filearg['filename']
            output_file = open(app_dir + '/' + original_fname, 'w')
            output_file.write(filearg['body'])
            driver_path = app_dir + '/' + original_fname

            status_file = update_status(driver_path, app_status=APP_STATUS['UPLOADED'])
            with open(status_file.name, 'rb') as f:
                self.write(f.readlines()[-1])
            f.close()


def mark_submitted(driver_path):
    """
    updates the STATUS_FILE with a new entry when job is submitted
    :param driver_path: the path to the main sparktk/pyspark script within the uploads folder
    :return: None
    """
    update_status(driver_path, app_status=APP_STATUS['SUBMITTED'])


def spark_submit(exec_string, log_file, driver_path):
    """
    asynchronously run the pyspark/sparktk submitted script while writing the logs to the log_file for the app
    :param exec_string: the command that is going to be run
    :param log_file: the file containing command(script) logs while running
    :param driver_path: the path to the main sparktk/pyspark script within the uploads folder
    :return: None
    """
    print "Entering spark_submit"
    mark_submitted(driver_path)
    pool = Pool(max_workers=1)
    cmd_string = "%s >>%s 2>&1" % (exec_string, log_file)
    print "CMD stting is %s" % (cmd_string)
    future = pool.submit(subprocess.call, cmd_string, shell=True)
    future.driver_path = driver_path
    future.add_done_callback(mark_completed)


def mark_completed(future):
    """
    once the application has finished running, updates the status_file with a new entry for COMPLETED
    :param future:
    :return: None
    """
    update_status(future.driver_path, app_status=APP_STATUS['COMPLETED'])


# TODO: this is only a workaround to ublock the spark-submit against sparktk apps while the bug is being fixed.
def get_sparktk_submit_jars():
    """
    spark-submit requires sparktk apps to provide values for both --jars and --driver-class-path options.
    This function finds these jars.
    :return: a list of strings and a string to be used for --jars and --driver-class-path command line option values
    """
    extns = ('.jar')
    sparktk_submit_jars = []

    for root, dirnames, fns in os.walk(os.environ['SPARK_HOME']):
        sparktk_submit_jars.extend(os.path.join(root, fn) for fn in fns if fn.lower().endswith(extns))
    for root, dirnames, fns in os.walk(os.environ['SPARKTK_HOME']):
        sparktk_submit_jars.extend(os.path.join(root, fn) for fn in fns if fn.lower().endswith(extns))
    sparktk_driver_class_path = \
        os.environ['SPARK_HOME'] + \
        "/lib/*:" + os.environ['SPARKTK_HOME'] \
        + "/*:" + os.environ['SPARKTK_HOME'] + \
        "/dependencies/*"

    return ','.join(sparktk_submit_jars), sparktk_driver_class_path


class SparkSubmitHandler(IPythonHandler):
    """
    implements the "spark-submit" REST api end point

    Examples:
        curl http://<JUPYTER_NOTEBOOK_URL>/spark-submit -d "driver-path=uploads/0001/frame-basics.py"
    """

    def post(self):
        driver_path = self.get_argument('driver-path')

        if (os.path.isfile(driver_path)):
            logfile = os.path.dirname(driver_path) + '/' + 'LOG.log'
            sparktk_submit_jars, sparktk_driver_class_path = get_sparktk_submit_jars()
            exec_string = 'spark-submit --jars %s --driver-class-path %s %s' % (
            sparktk_submit_jars, sparktk_driver_class_path, driver_path)
            spark_submit(exec_string, logfile, driver_path)
            self.write("SparkSubmit Job Queued\n")
        else:
            self.write("The given path %s is not a valid script" % (driver_path))


class LogHandler(IPythonHandler):
    """
    implements the "logs" REST api endpoint.

    Examples:
        curl http://<JUPYTER_NOTEBOOK_URL>/logs -d "app-path=uploads/0001" -d "offset=1" -d "n=100"
    """

    def post(self):
        app_path = self.get_argument('app-path')
        offset_str = self.get_argument('offset', '0', True)
        num_lines_str = self.get_argument('n', '10', True)

        try:
            offset = int(offset_str)
            num_lines = int(num_lines_str)
        except ValueError:
            self.write("both offset and n must be integers.")
            return

        logfile = app_path + '/' + LOG_FILE
        if (os.path.exists(app_path) and os.path.isfile(logfile)):
            with open(logfile, 'rb') as f:
                for i, line in enumerate(f):
                    if (i < offset):
                        pass
                    elif (num_lines < 0 or i < offset + num_lines):
                        self.write(line)
        else:
            self.write("Error, app-path %s doesn't exist or no logs exist yet" % (app_path))


class StatusHandler(IPythonHandler):
    """
    implements the "logs" REST api endpoint.

    Examples:
        curl http://<JUPYTER_NOTEBOOK_URL>/status -d "app-path=uploads/0001"
    """

    def post(self):
        app_path = self.get_argument('app-path')

        status_file = app_path + '/' + STATUS_FILE
        if (os.path.exists(app_path) and os.path.isfile(status_file)):
            with open(status_file, 'rb') as f:
                for i, line in enumerate(f):
                    pass
                self.write(line)
        else:
            self.write("Error, app-path %s doesn't exist or no status exist yet" % (app_path))


class RenameHandler(IPythonHandler):
    """
    implements the "rename" REST api endpoint.

    Examples:
        curl http://<JUPYTER_NOTEBOOK_URL>/rename -d "app-path=uploads/0001" -d "dst-path=uploads/myapp"
    """

    def post(self):
        app_path = self.get_argument('app-path')
        dst_path = self.get_argument('dst-path')
        status_file_path = app_path + '/' + STATUS_FILE
        if (os.path.exists(app_path) and os.path.isfile(status_file_path)):
            with open(status_file_path, 'rb') as f:
                if not (json.loads(f.readlines()[-1])['app-status'] == APP_STATUS['SUBMITTED']):
                    os.rename(app_path, dst_path)
                    self.write('the new path for the app is %s' % (dst_path))
                else:
                    self.write("Error, directory %s is in use, please try later" % (app_path))
        else:
            self.write("Error, app-path %s doesn't exist or not a valid path" % (app_path))


class DeleteHandler(IPythonHandler):
    """
    implements the "delete" REST api endpoint.

    Examples:
        curl http://<JUPYTER_NOTEBOOK_URL>/delete -d "app-path=uploads/0001"
    """

    def post(self):
        app_path = self.get_argument('app-path')
        status_file_path = app_path + '/' + STATUS_FILE
        if (os.path.exists(app_path)) and os.path.isfile(status_file_path):
            with open(status_file_path, 'rb') as f:
                if not (json.loads(f.readlines()[-1])['app-status'] == APP_STATUS['SUBMITTED']):
                    # TODO: Once jupyter image size is not an issue remove this and user shutil module
                    for root, dirs, files in os.walk(top=app_path, topdown=False):
                        for name in files:
                            os.remove(os.path.join(root, name))
                        for name in dirs:
                            os.rmdir(os.path.join(root, name))
                    os.rmdir(app_path)
                    self.write("The app directory %s was successfully deleted" % (app_path))
                else:
                    self.write("Error, directory %s is in use, please try later" % (app_path))
        else:
            self.write("Pass, app-path %s doesn't exist or not a valid path. No action is needed." % (app_path))


def load_jupyter_server_extension(nb_app):
    '''
    Based on https://github.com/Carreau/jupyter-book/blob/master/extensions/server_ext.py
    '''
    web_app = nb_app.web_app
    host_pattern = '.*$'
    web_app.settings["jinja2_env"].loader.searchpath += [
        os.path.join(os.path.dirname(__file__), "templates")
    ]
    web_app.add_handlers(host_pattern,
                         host_handlers=[
                             (r"/hello", IndexHandler),
                             (r"/upload", UploadHandler),
                             (r"/spark-submit", SparkSubmitHandler),
                             (r"/rename", RenameHandler),
                             (r"/delete", DeleteHandler),
                             (r"/logs", LogHandler),
                             (r"/status", StatusHandler),
                         ]
                         )
