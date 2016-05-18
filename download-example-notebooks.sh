#!/bin/bash
# Script for downloading the latest notebooks from github

BRANCH=master
# Setup temporary directory
TEMP_DIR=/tmp/tap-notebook-update
if [ -d $TEMP_DIR ]
then
   # Remove the old one if it exists
   rm -rf $TEMP_DIR
fi
mkdir -p $TEMP_DIR

# Download the latest files from github
curl -L https://github.com/trustedanalytics/jupyter-default-notebooks/archive/${BRANCH}.zip > $TEMP_DIR/notebooks.zip

pushd $TEMP_DIR

unzip notebooks.zip

# copy the example notebooks
cp -rv jupyter-default-notebooks-${BRANCH}/notebooks/* ~/jupyter

# Remove temporary directory
rm -rf $TEMP_DIR
