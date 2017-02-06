FROM debian:jessie


ENV DEBIAN_FRONTEND noninteractive


# Add contrib repository
RUN sed -i 's/$/ contrib/g' /etc/apt/sources.list

# Install required software and tools
RUN \
    apt-get update && \
    apt-get -y upgrade && \
    apt-get install -yq --no-install-recommends --fix-missing \
    bzip2 \
    locales \
    tar \
    unzip \
    vim.tiny \
    wget


# Setup en_US locales to handle non-ASCII characters correctly
ENV LC_ALL en_US.UTF-8
ENV LANGUAGE en_US.UTF-8
ENV LANG en_US.UTF-8
ENV dpkg-reconfigure locales
RUN \
    echo "en_US.UTF-8 UTF-8" > /etc/locale.gen && \
    locale-gen


# Add jessie-backports repository to install JDK 1.8
RUN \
    echo "===> add jessie-backports repository ..." && \
    echo "deb http://ftp.debian.org/debian jessie-backports main" | tee /etc/apt/sources.list.d/openjdk-8-jdk.list && \
    apt-get update && \
    echo "===> install Java" && \
    apt install -t jessie-backports -yq --no-install-recommends --fix-missing openjdk-8-jre-headless ca-certificates-java openjdk-8-jdk


# define default command
CMD ["java"]


# Install Tini
ARG TINI_VERSION="v0.13.0"
ADD https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini /usr/bin/
RUN chmod +x /usr/bin/tini


# Create vcap user with UID=1000 and in the 'users' group
ENV SHELL /bin/bash
ENV NB_USER vcap
ENV NB_UID 1000
ENV HOME /home/$NB_USER
RUN useradd -m -s /bin/bash -d $HOME -N -u $NB_UID $NB_USER
ENV CONDA_DIR /opt/anaconda2
RUN mkdir -p $CONDA_DIR 


# Download and Install Miniconda
ARG CONDA_VERSION="2-4.2.12"
RUN \
    wget -q --no-check-certificate https://repo.continuum.io/miniconda/Miniconda${CONDA_VERSION}-Linux-x86_64.sh -P $CONDA_DIR && \
    bash $CONDA_DIR/Miniconda${CONDA_VERSION}-Linux-x86_64.sh -f -b -p $CONDA_DIR && \
    rm -rf $CONDA_DIR/Miniconda${CONDA_VERSION}*x86_64.sh 

#Add conda binaries to path
ENV PATH $CONDA_DIR/bin:$PATH
   

# Setup vcap home directory
RUN \
    mkdir $HOME/work && \
    mkdir $HOME/.jupyter && \
    mkdir $HOME/.local && \
    echo "cacert=/etc/ssl/certs/ca-certificates.crt" > $HOME/.curlrc


# Configure container startup
EXPOSE 8888
WORKDIR $HOME/jupyter
RUN mkdir -p $HOME/jupyter 


COPY assets/start-notebook.sh /usr/local/bin/
COPY assets/jupyter_notebook_config.py $HOME/.jupyter/
ENTRYPOINT ["tini", "--"]
CMD ["start-notebook.sh"]


# Copy all files before switching users
COPY assets/tapmenu/ $HOME/tapmenu
# Install Python 2 packages and kernel spec
RUN \
    conda install --yes \
    'curl' \
    'lxml' \
    'notebook=<4.2.3' && \
     conda clean --all


# This logo gets displayed within our default notebooks
RUN \
    jupyter-nbextension install $HOME/tapmenu && \
    jupyter-nbextension enable tapmenu/main
COPY assets/TAP-logo.png $CONDA_DIR/lib/python2.7/site-packages/notebook/static/base/images


# Final apt cleanup
RUN apt-get purge -y 'python3.4*' && \
    apt-get -yq autoremove && \
    apt-get -yq autoclean && \
    rm -rf /var/lib/apt/lists/* && \
    conda clean -y --all
    

RUN mkdir -p $HOME/.jupyter/nbconfig


######### End of Jupyter Base ##########


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
    chown -R $NB_USER:users /user/spark


# Fix the entry point
COPY ./jupyter-startup.sh /usr/local/bin/jupyter-startup.sh
RUN chmod +x /usr/local/bin/jupyter-startup.sh
CMD ["/usr/local/bin/jupyter-startup.sh"]


RUN mkdir -p $HOME/.jupyter/nbconfig


# Install Python 2 packages and kernel spec
RUN \
    conda install --yes \
    'pip>=9.0.1' \
    'freetype' \
    'matplotlib>=1.5*' \
    'nomkl' \
    'pandas>=0.18*' \
    'pymongo' \
    'pyzmq' \
    'scikit-learn>=0.17*' \
    'scipy>=0.17*' \
    'futures' && \
     conda clean --all


# Install Python 2 kernelspec into conda environment
COPY jupyter-default-notebooks/notebooks $HOME/jupyter
RUN $CONDA_DIR/bin/python -m ipykernel.kernelspec --prefix=$CONDA_DIR


# Create a symbolick link for pip2.7 between now and upgrade to Python3
RUN ln -s $CONDA_DIR/bin/pip $CONDA_DIR/bin/pip2.7


# Set required paths for spark-tk/daal-tk packages
ENV SPARKTK_HOME "/usr/local/sparktk-core"
ENV DAALTK_HOME "/usr/local/daaltk-core"
ENV LD_LIBRARY_PATH /usr/local/daal-2016.2.181:$LD_LIBRARY_PATH
ARG TKLIBS_INSTALLER_URL="https://github.com/trustedanalytics/daal-tk/releases/download/v0.7.4/daal-install"
ARG TKLIBS_INSTALLER="daal-install"


# Install spark-tk/daal-tk packages
#ADD $TKLIBS_INSTALLER_URL /usr/local/
RUN cd /usr/local && \ 
    wget -q --no-check-certificate $TKLIBS_INSTALLER_URL && \
    chmod +x $TKLIBS_INSTALLER  && \
    sync && \
    ./$TKLIBS_INSTALLER && \
    ln -s /usr/local/sparktk-core-* $SPARKTK_HOME && \
    ln -s /usr/local/daaltk-core-* $DAALTK_HOME && \
    rm -rf /usr/local/$TKLIBS_INSTALLER /usr/local/*.tar.gz


# Install spark-tk package mainly to fix the graphframes install
RUN cd $SPARKTK_HOME && \
    chmod +x install.sh && \
    sync && \
    ./install.sh


# copy misc modules for TAP to python2.7 site-packages
COPY misc-modules/* $CONDA_DIR/lib/python2.7/site-packages/


# enable jupyter server extention for sparktk
RUN jupyter serverextension enable sparktk_ext


# Install remaining tk packages
RUN \
    pip install trustedanalytics \
    tabulate==0.7.5 \
    snakebite==2.11.0 


# Final cleanup
RUN \
    rm -rf /tmp/* && \
    rm -rf $HOME/jupyter/examples/pandas-cookbook/Dockerfile && \
    rm -rf $HOME/jupyter/examples/pandas-cookbook/README.md 

