FROM quay.io/trustedanalytics/jupyter-base

MAINTAINER TAP Dev-Ops Team

USER root

# Util to help with kernel spec later
RUN apt-get -y update && apt-get -y install && apt-get clean && rm -rf /var/lib/apt/lists/*

# Spark dependencies
ENV APACHE_SPARK_VERSION 1.5.0
RUN apt-get -y update && \
    apt-get install -y --no-install-recommends && \
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
ENV SPARK_CONF_DIR "/etc/spark/conf"
ENV HADOOP_CONF_DIR "/etc/hadoop/conf"
ENV YARN_CONF_DIR $HADOOP_CONF_DIR

# Creating these directories and links to better match cloudera layout
RUN mkdir -p /etc/spark/conf.cloudera.spark
RUN mkdir -p /etc/hadoop/conf.cloudera.yarn
RUN ln -s /etc/spark/conf.cloudera.spark $SPARK_CONF_DIR
RUN ln -s /etc/hadoop/conf.cloudera.yarn $HADOOP_CONF_DIR

# Cloudera config is expecting a classpath.txt
RUN ls $SPARK_HOME/lib/* > $SPARK_CONF_DIR/classpath.txt

RUN mkdir -p /user/spark/applicationHistory

RUN chown -R $NB_USER:users /etc/hadoop /etc/spark /user/spark

COPY ./jupyter-startup.sh /usr/local/bin/jupyter-startup.sh
RUN chmod +x /usr/local/bin/jupyter-startup.sh
CMD ["/usr/local/bin/jupyter-startup.sh"]

USER $NB_USER

# Install Python 2 packages and kernel spec
RUN conda install --yes \
    'ipython=4.1*' \
    'ipywidgets=4.1*' \
    'pandas=0.18*' \
    'matplotlib=1.5*' \
    'scipy=0.17*' \
    'seaborn=0.7*' \
    'scikit-learn=0.17*' \
    'ipykernel' \
    'pyzmq' \
    'freetype' \
    && conda clean --all

# Install Python 2 kernel spec into conda environment
USER root
RUN $CONDA_DIR/bin/python -m ipykernel.kernelspec --prefix=$CONDA_DIR

RUN chown -R $NB_USER:users $CONDA_DIR/share/

ADD jupyter-default-notebooks/notebooks/ $WORKDIR

RUN chown -R $NB_USER:users /home/$NB_USER/jupyter
RUN rm -rf /home/$NB_USER/jupyter/examples/pandas-cookbook/Dockerfile

USER $NB_USER

