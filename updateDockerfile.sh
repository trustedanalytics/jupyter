#!/bin/bash

chmod +x git-asset

URL=$(./git-asset -t $GIT_TOKEN -o trustedanalytics -r spark-tk download  --artifact-type sparktk-java --release-type RC)
echo $URL
SPARKTK_ZIP_NAME=$(echo $URL | tr "/" " " | awk '{print $NF}')
SPARKTK_NAME=$(echo $SPARKTK_ZIP_NAME | sed -e "s|.zip||g" )
echo spark zip name $SPARKTK_ZIP_NAME
echo spark name $SPARKTK_NAME
#SPARKTK_ZIP=$(find . -name "sparktk-core*.zip")


echo $SPARKTK_ZIP
sed -i "s|ENV SPARKTK_ZIP_URL.*|ENV SPARKTK_ZIP_URL  $URL|g" Dockerfile
sed -i "s|ENV SPARKTK_ZIP_PACKAGE_NAME.*|ENV SPARKTK_ZIP_PACKAGE_NAME $SPARKTK_ZIP_NAME|g" Dockerfile
sed -i "s|ENV SPARKTK_ZIP_FOLDER_NAME.*|ENV SPARKTK_ZIP_FOLDER_NAME $SPARKTK_NAME|g" Dockerfile
git status

git diff Dockerfile

git commit -m "update sparktk build" Dockerfile 

if [ "$BRANCH" != "" ]; then
echo git tag -a $BRANCH -m "BRANCH build"
git tag -a $BRANCH  -m "$BRANCH build"

echo git push origin $BRANCH
git push origin $BRANCH
fi
