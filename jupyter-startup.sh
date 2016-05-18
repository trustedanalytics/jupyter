#!/bin/bash
export CDH_CONFIG_DIR="/tmp/cdh-configs"
mkdir ${CDH_CONFIG_DIR}

pushd ${CDH_CONFIG_DIR}

if [ ! -z "$SPARK_ON_YARN_CLIENT_CONFIG" ]; then
	curl ${SPARK_ON_YARN_CLIENT_CONFIG} > spark.zip
	unzip spark.zip
	cp spark-conf/* $SPARK_CONF_DIR
	cp yarn-conf/* $HADOOP_CONF_DIR
        
	# Fix bad variables
	sed -i -e "s#{{SPARK_HOME}}#$SPARK_HOME#g" $SPARK_CONF_DIR/spark-env.sh
	sed -i -e "s#{{PYTHON_PATH}}#$PYTHON_PATH#g" $SPARK_CONF_DIR/spark-env.sh
        # Other bad patterns we might need to fix:
        #  {{HADOOP_HOME}}
	#  {{SPARK_JAR_HDFS_PATH}}
	#  {{SPARK_EXTRA_LIB_PATH}}

	# Fix bad permissions
	chmod +x $HADOOP_CONF_DIR/topology.py

	# Fix bad setting
	sed -i -e 's#/etc/hadoop/conf.cloudera.*/topology.py#/etc/hadoop/conf/topology.py#g' $HADOOP_CONF_DIR/core-site.xml

	# Make sure event log is disabled
	sed -i -e 's#spark.eventLog.enabled=true#spark.eventLog.enabled=false#g' $SPARK_CONF_DIR/spark-defaults.conf
fi
popd

unset CDH_CONFIG_DIR
source /usr/local/bin/start-notebook.sh
