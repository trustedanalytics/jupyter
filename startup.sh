#!/bin/bash
export CDH_CONFIG_DIR="/tmp/cdh-configs"
mkdir ${CDH_CONFIG_DIR}

pushd ${CDH_CONFIG_DIR}

if [ ! -z "$SPARK_ON_YARN_CLIENT_CONFIG" ]; then
	curl ${SPARK_ON_YARN_CLIENT_CONFIG} > spark.zip
	unzip spark.zip
	mkdir -p $SPARK_CONF_DIR
	mkdir -p $HADOOP_CONF_DIR
	cp spark-conf/* $SPARK_CONF_DIR
	cp hadoop-conf $HADOOP_CONF_DIR
fi;
popd

unset CDH_CONFIG_DIR
source /usr/local/bin/start-notebook.sh
