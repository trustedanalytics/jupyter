#!/bin/bash

chmod +x git-asset

URL=$(./git-asset -t $GIT_TOKEN -o trustedanalytics -r spark-tk download  --artifact-type sparktk-java --release-type RC)
echo $URL

SPARKTK_ZIP=$(find `pwd` -name "sparktk-core*.zip")

echo $SPARKTK_ZIP
sed "s|SPARKTK_ZIP=.*|run wget $SPARKTK_ZIP |g" Dockerfile

git status

