NAME="[`basename $BASH_SOURCE[0]`]"
DIR="$( cd "$( dirname "$BASH_SOURCE[0]" )" && pwd )"

target=/user/$USER

sudo -u hdfs hdfs dfs -mkdir -p $target
sudo -u hdfs hdfs dfs -mkdir -p $target/qa_data
sudo -u hdfs hdfs dfs -mkdir -p $target/qa_data/temp

sudo -u hdfs hdfs dfs -chown $USER:$USER $target
sudo -u hdfs hdfs dfs -chown $USER:$USER $target/qa_data
sudo -u hdfs hdfs dfs -chown $USER:$USER $target/qa_data/temp
hdfs dfs -put -f $DIR/../datasets/* $target/qa_data/temp
echo "$DIR/../datasets/*"
