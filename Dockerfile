# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
FROM quay.io/trustedanalytics/jupyter-base

MAINTAINER Jupyter Project <jupyter@googlegroups.com>

USER root

# Util to help with kernel spec later
RUN apt-get -y update && apt-get -y install jq && apt-get clean && rm -rf /var/lib/apt/lists/*

# Spark dependencies
ENV APACHE_SPARK_VERSION 1.5.0
RUN apt-get -y update && \
    apt-get install -y --no-install-recommends openjdk-7-jre-headless && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
RUN cd /tmp && \
        wget -q http://www.apache.org/dist/spark/spark-${APACHE_SPARK_VERSION}/spark-${APACHE_SPARK_VERSION}-bin-hadoop2.6.tgz && \
        echo "d8d8ac357b9e4198dad33042f46b1bc09865105051ffbd7854ba272af726dffc *spark-${APACHE_SPARK_VERSION}-bin-hadoop2.6.tgz" | sha256sum -c - && \
        tar xzf spark-${APACHE_SPARK_VERSION}-bin-hadoop2.6.tgz -C /usr/local && \
        rm spark-${APACHE_SPARK_VERSION}-bin-hadoop2.6.tgz
RUN cd /usr/local && ln -s spark-${APACHE_SPARK_VERSION}-bin-hadoop2.6 spark

# Spark pointers
ENV SPARK_HOME /usr/local/spark
ENV PYTHONPATH $SPARK_HOME/python:$SPARK_HOME/python/lib/py4j-0.8.2.1-src.zip
ENV PATH $SPARK_HOME/bin:$PATH

USER $NB_USER

# Install Python 2 packages and kernel spec
RUN conda install --yes \
    'ipython=4.1*' \
    'ipywidgets=4.1*' \
    'pandas=0.17*' \
    'matplotlib=1.5*' \
    'scipy=0.17*' \
    'seaborn=0.7*' \
    'scikit-learn=0.17*' \
    'ipykernel' \
    'pyzmq' \
    && conda clean --all

# Install Python 2 kernel spec into the Python 3 conda environment which
USER root
RUN $CONDA_DIR/bin/python -m ipykernel.kernelspec --prefix=$CONDA_DIR

# Create PySPARK in Local mode entry for Jupyter
RUN mkdir -p $CONDA_DIR/share/jupyter/kernels/Py2SPARK-Local/
COPY Py2SPARK.json $CONDA_DIR/share/jupyter/kernels/Py2SPARK-Local/kernel.json
RUN chown -R $NB_USER:users $CONDA_DIR/share/

USER $NB_USER

