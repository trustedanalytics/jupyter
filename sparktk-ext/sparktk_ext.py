import errno
import json
import os
import select
import subprocess
import time

from notebook.base.handlers import IPythonHandler

STATUS_FILE = 'STATUS.log'
LOG_FILE = 'LOG.log'

APP_STATUS = {
    'uploaded': 'uploaded',
    'submitted': 'submitted',
    'completed': 'completed'
}

SETTINGS = {
    'template_path': r"templates",
    'static_path': r"templates/static",
    'uploads_path': r"uploads",
    "xsrf_cookies": False
}

RESPONSE = {
    "driver_path": 'driver-path',  # submitted app id
    "app_status": 'app-status',  # uploaded, running, completed
    "app_dir": 'app-dir',  # Path where the app bits are uploaded
    "last_updated" : "last-updated" # The time and date of last status update
}


def update_status(driver_path, app_status='uploaded'):
    app_dir = os.path.dirname(driver_path)
    status_file = open(os.path.dirname(driver_path) + '/' + STATUS_FILE, 'a+w')
    status_file.write('\n')
    status_file.write(json.dumps(
        dict(
            {
                RESPONSE['driver_path']: driver_path,
                RESPONSE['app_status']: app_status,
                RESPONSE['app_dir']: app_dir,
                RESPONSE['last_updated'] : time.strftime("%c")
            }
        )
    ))
    status_file.close()
    return status_file


class IndexHandler(IPythonHandler):
    def get(self):
        self.write("Hello From Jupyter")

    def write_error(self, status_code, **kwargs):
        self.write("Gosh darnit, user! You caused a %d error." % status_code)


class UploadFormHandler(IPythonHandler):
    def get(self):
        self.render("templates/fileuploadform.html")


class UploadHandler(IPythonHandler):
    def create_upload_dir(self):
        max_dir_len = len('0000')
        i = 0
        dir_name = SETTINGS['uploads_path'] + '/%s' % str(i).zfill(max_dir_len)
        while os.path.exists(dir_name) and (i < 10 ** max_dir_len):
            i += 1
            dir_name = SETTINGS['uploads_path'] + '/%s' % str(i).zfill(max_dir_len)

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

            status_file = update_status(driver_path, app_status='uploaded')
            with open(status_file.name, 'rb') as f:
                self.write(f.readlines()[-1])
            f.close()


class SparkSubmitHandler(IPythonHandler):
    def post(self):
        driver_path = self.get_argument('driver-path')
        debug = self.get_argument('debug', 'no', True).lower()

        if not os.path.isfile(driver_path):
            raise Exception("The given path %s is not a valid script" % (driver_path))

        logfile = open(os.path.dirname(driver_path) + '/' + 'LOG.log', 'a+w+b')

        proc = subprocess.Popen(
            'spark-submit %s' % (driver_path),
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )

        status_file = update_status(driver_path, app_status='submitted')
        with open(status_file.name, 'rb') as f:
            self.write(f.readlines()[-1])
            f.close()

        while proc.poll() is None:
            time.sleep(1)
            for line in iter(lambda: proc.stderr.readline(), ''):
                if debug == 'yes':
                    self.write(line)
                logfile.write(line)
            for line in iter(lambda: proc.stdout.readline(), ''):
                self.write(line)
                logfile.write(line)

        logfile.close()

        status_file = update_status(driver_path, app_status='completed')
        with open(status_file.name, 'rb') as f:
            self.write(f.readlines()[-1])
            f.close()


class LogHandler(IPythonHandler):
    def post(self):
        app_path = self.get_argument('app-path')
        status_file_path = app_path + '/' + STATUS_FILE
        logfile = app_path + '/' + LOG_FILE
        if (os.path.exists(app_path)) and os.path.isfile(status_file_path):
            with open(status_file_path, 'rb') as f:
                while (json.loads(f.readlines()[-1])['app-status'] == APP_STATUS['submitted']):
                    proc = subprocess.Popen(
                        ['tail', '-F', logfile],
                        shell=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        universal_newlines=True
                    )
                    p = select.poll()
                    p.register(proc.stderr)

                    while True:
                        if p.poll(1):
                            self.write(proc.stdout.readline())
                        time.sleep(1)
                else:
                    self.write("Error, the app in path %s is not in running state" % (app_path))
        else:
            self.write("Error, app-path %s doesn't exist or not a valid path" % (app_path))


class RenameHandler(IPythonHandler):
    def post(self):
        app_path = self.get_argument('app-path')
        dst_path = self.get_argument('dst-path')
        status_file_path = app_path + '/' + STATUS_FILE
        if (os.path.exists(app_path)) and os.path.isfile(status_file_path):
            with open(status_file_path, 'rb') as f:
                if not (json.loads(f.readlines()[-1])['app-status'] == APP_STATUS['submitted']):
                    os.rename(app_path, dst_path)
                    self.write('the new path for the app is %s' % (dst_path))
                else:
                    self.write("Error, directory %s is in use, please try later" % (app_path))
        else:
            self.write("Error, app-path %s doesn't exist or not a valid path" % (app_path))


class DeleteHandler(IPythonHandler):
    def post(self):
        app_path = self.get_argument('app-path')
        status_file_path = app_path + '/' + STATUS_FILE
        if (os.path.exists(app_path)) and os.path.isfile(status_file_path):
            with open(status_file_path, 'rb') as f:
                if not (json.loads(f.readlines()[-1])['app-status'] == APP_STATUS['submitted']):
                    # TODO: Once jupyter image size is not an issue remove this and user shutil module
                    for root, dirs, files in os.walk(top=app_path, topdown=False):
                        for name in files:
                            os.remove(os.path.join(root, name))
                        for name in dirs:
                            os.rmdir(os.path.join(root, name))
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
                             # (r"/logs", LogHandler),
                         ]
                         )
