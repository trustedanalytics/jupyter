#!/bin/bash
export CDH_CONFIG_DIR="/tmp/cdh-configs"
mkdir ${CDH_CONFIG_DIR}

pushd ${CDH_CONFIG_DIR}

if [ ! -z "$SPARK_ON_YARN_CLIENT_CONFIG" ]; then
	curl ${SPARK_ON_YARN_CLIENT_CONFIG} > spark.zip
	unzip spark.zip
	cp spark-conf/* -p $SPARK_CONF_DIR
	cp hadoop-conf -p $HADOOP_CONF_DIR
fi;
popd

source /usr/local/bin/start-notebook.sh
