
#jupyter

Docker image for Jupyter on TAP.

Two images are used:
- jupyter-base - includes the parts that rarely change, e.g. 3rd party libraries
- jupyter (this project) - includes most of our customizations and is layered on top of the jupyter-base

The image was split into two parts for faster builds and deploys.

##Features

- PySpark
- ATK libraries
- Anaconda
- TAP Help menus
- Examples from the project jupyter-default-notebooks
