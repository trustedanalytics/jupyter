#!/bin/bash
export CDH_CONFIG_DIR="/tmp/cdh-configs"
mkdir ${CDH_CONFIG_DIR}

pushd ${CDH_CONFIG_DIR}

if [ ! -z "$SPARK_ON_YARN_CLIENT_CONFIG" ]; then
	curl ${SPARK_ON_YARN_CLIENT_CONFIG} > spark.zip
	unzip spark.zip
	cp spark-conf/* $SPARK_CONF_DIR
	cp yarn-conf/* $HADOOP_CONF_DIR
        
	#Fix bad variables
	sed -i  -e "s#{{SPARK_HOME}}#$SPARK_HOME#g" $SPARK_CONF_DIR/spark-env.sh

	# Fix bad permissions
	chmod +x $HADOOP_CONF_DIR/topology.py
fi
popd

unset CDH_CONFIG_DIR
source /usr/local/bin/start-notebook.sh
