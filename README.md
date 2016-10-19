
#jupyter

Docker image for Jupyter on TAP.

Two images are used:
- jupyter-base - includes the parts that rarely change, e.g. 3rd party libraries
- jupyter (this project) - includes most of our customizations and is layered on top of the jupyter-base

The image was split into two parts for faster builds and deploys.

## Building the image
- Build the jupyter-base image first and tag it
- Pull all the submodules: git submodule update --init --recursive
- Update the the Dockerfile where it reads: FROM "quay.io/trustedanalytics/jupyter-base" to point to your jupyter-base image tag
- sudo docker build .
- Or if you are behind a proxy use this:
- sudo docker build --build-arg HTTP_PROXY=$http_proxy --build-arg HTTPS_PROXY=$http_proxy --build-arg NO_PROXY=$no_proxy --build-arg http_proxy=$http_proxy --build-arg https_proxy=$http_proxy --build-arg no_proxy=$no_proxy .

## Run the image:
- sudo docker run -p 8900:8888 YOUR_JUPYTER_IMAGE_TAG

##Features

- PySpark, Spark Shell
- Jupyter REST API's for upload and running PySpark/SparkTK scripts
- ATK libraries
- Spark-TK libraries
- Anaconda 2.7
- TAP Help menus
- Examples notebooks from the project jupyter-default-notebooks

## REST API's provided

### upload
- currently the only way to upload files to Jupyter is using the upload Form.
    after each attemp to upload the file(s) are loaded into a directory format like "uploads/dddd" where d is a digit.

- curl http://JUPYTER_NOTEBOOK_URL/upload -F "filearg=@/home/ashahba/frame-basics.py"
- curl http://JUPYTER_NOTEBOOK_URL/upload -F "filearg=@/home/ashahba/frame-basics.py" -F "filearg=@/home/ashahba/frame-advanced.py"

### delete
- curl http://JUPYTER_NOTEBOOK_URL/delete -d "app-path=uploads/0001"

### rename
- curl http://JUPYTER_NOTEBOOK_URL/rename -d "app-path=uploads/0001" -d "dst-path=uploads/myapp"

### spark-submit
- curl http://JUPYTER_NOTEBOOK_URL/spark-submit -d "driver-path=uploads/0001/frame-basics.py"

### logs
- curl http://JUPYTER_NOTEBOOK_URL/logs -d "app-path=uploads/0001" -d "offset=1" -d "n=100"

### status
- curl http://JUPYTER_NOTEBOOK_URL/status -d "app-path=uploads/0001"

