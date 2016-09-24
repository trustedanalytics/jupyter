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


# Remove un-needed files
RUN \
    rm -rf /home/$NB_USER/jupyter/examples/pandas-cookbook/Dockerfile && \
    rm -rf /home/$NB_USER/jupyter/examples/pandas-cookbook/README.md && \
    rm -rf `find $CONDA_DIR -name tests -type d` && \
    rm -rf `find $CONDA_DIR -name test -type d` && \
    rm -rf `find $COND_DIR -name "*.pyc"`


# Install trustedanalytics-python-client and do a final cleanup
USER $NB_USER
RUN pip install trustedanalytics

