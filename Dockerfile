FROM quay.io/trustedanalytics/jupyter-base

MAINTAINER TAP Dev-Ops Team

USER root


# Install Spark dependencies
ENV APACHE_SPARK_VERSION 1.6.0
RUN \
    wget -q http://archive.apache.org/dist/spark/spark-${APACHE_SPARK_VERSION}/spark-${APACHE_SPARK_VERSION}-bin-hadoop2.6.tgz -P /usr/local && \
    tar xzf /usr/local/spark-${APACHE_SPARK_VERSION}-bin-hadoop2.6.tgz -C /usr/local && \
    rm -rf /usr/local/spark-${APACHE_SPARK_VERSION}-bin-hadoop2.6.tgz && \
    ln -s /usr/local/spark-${APACHE_SPARK_VERSION}-bin-hadoop2.6 /usr/local/spark


# Spark pointers
ENV SPARK_HOME /usr/local/spark
ENV PYTHONPATH $SPARK_HOME/python:$SPARK_HOME/python/lib/py4j-0.9-src.zip:/opt/cloudera/parcels/CDH/lib/spark/python/lib
ENV PYSPARK_PYTHON python2.7
ENV PATH $SPARK_HOME/bin:$PATH
ENV SPARK_CONF_DIR "/etc/spark/conf"
ENV HADOOP_CONF_DIR "/etc/hadoop/conf"
ENV YARN_CONF_DIR $HADOOP_CONF_DIR
RUN mkdir -p $SPARK_CONF_DIR && \
    mkdir -p $HADOOP_CONF_DIR


# Cloudera config is expecting a classpath.txt, also fix some permissions
RUN ls $SPARK_HOME/lib/* > $SPARK_CONF_DIR/classpath.txt && \
    mkdir -p /user/spark/applicationHistory && \
    chown -R $NB_USER:users /etc/hadoop /etc/spark /user/spark /usr/local/share/jupyter


# Fix the entry point
COPY ./jupyter-startup.sh /usr/local/bin/jupyter-startup.sh
RUN chmod +x /usr/local/bin/jupyter-startup.sh
CMD ["/usr/local/bin/jupyter-startup.sh"]


USER $NB_USER
RUN mkdir -p $HOME/.jupyter/nbconfig


# Install Python 2 packages and kernel spec
RUN \
    conda install --yes \
    'freetype' \
    'matplotlib>=1.5*' \
    'nomkl' \
    'pandas>=0.18*' \
    'pymongo' \
    'pyzmq' \
    'scikit-learn>=0.17*' \
    'scipy>=0.17*' && \
     conda clean --all


# Install Python 2 kernelspec into conda environment
USER root
COPY jupyter-default-notebooks/notebooks $HOME/jupyter
RUN \
    $CONDA_DIR/bin/python -m ipykernel.kernelspec --prefix=$CONDA_DIR && \
    chown -R $NB_USER:users $HOME/jupyter


# Set required paths for spark-tk and install the packages
ENV SPARKTK_HOME /usr/local/sparktk-core
ENV SPARKTK_ZIP_URL  https://github.com/trustedanalytics/spark-tk/releases/download/v0.7.3rc1/sparktk-core-0.7.3.rc1772.zip
ENV SPARKTK_ZIP_PACKAGE_NAME sparktk-core-0.7.3.rc1772.zip
ENV SPARKTK_ZIP_FOLDER_NAME sparktk-core-0.7.3.rc1772
RUN wget $SPARKTK_ZIP_URL   -O /usr/local/$SPARKTK_ZIP_PACKAGE_NAME --no-check-certificate
ARG SPARKTK_MODULE_ARCHIVE="$SPARKTK_HOME/python/sparktk-*.tar.gz"
RUN unzip /usr/local/$SPARKTK_ZIP_PACKAGE_NAME -d /usr/local/ && \
    rm -rf /usr/local/$SPARKTK_ZIP_PACKAGE_NAME && \
    ln -s /usr/local/sparktk-core-* $SPARKTK_HOME && \
    cd $SPARKTK_HOME; ./install.sh


# Install trustedanalytics-python-client and spark-tk module
USER $NB_USER
RUN \
    pip install $SPARKTK_MODULE_ARCHIVE


## install Graphframe dependencies
#RUN \
#    unzip -o $SPARKTK_HOME/lib/graphframes-*-spark*.jar "graphframes/*" && \
#    cp -rp graphframes $CONDA_DIR/lib/python2.7/site-packages/ && \
#    rm -rf graphframes 


# copy hdfsclient.py to python2.7 site-packages
COPY hdfsclient.py $CONDA_DIR/lib/python2.7/site-packages/
COPY tap_catalog.py $CONDA_DIR/lib/python2.7/site-packages/


# enable jupyter server extention for sparktk
COPY sparktk-ext/* $CONDA_DIR/lib/python2.7/site-packages/
RUN jupyter serverextension enable sparktk_ext


USER root
RUN \
    rm -rf /tmp/* && \
    rm -rf /home/$NB_USER/jupyter/examples/pandas-cookbook/Dockerfile && \
    rm -rf /home/$NB_USER/jupyter/examples/pandas-cookbook/README.md


USER $NB_USER
RUN \
    pip install trustedanalytics && \
    tabulate==0.7.5 && \
    snakebite==2.11.0

