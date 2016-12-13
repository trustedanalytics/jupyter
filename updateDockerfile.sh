#!/bin/bash
BRANCH=$(echo $BRANCH | sed -e "s|tags/||g")
DOCKER_UPDATE_BRANCH="docker-update"

chmod +x git-asset

DAALTK_URL=$(./git-asset -t $GIT_TOKEN -o trustedanalytics -r daal-tk download  --artifact-type daaltk-installer --release-type RC)
echo $DAALTK_URL
sed -i "s|ARG TKLIBS_INSTALLER_URL=.*|ARG TKLIBS_INSTALLER_URL=\"$DAALTK_URL\"|g" Dockerfile

git clone git@github.com:trustedanalytics/jupyter.git -b $DOCKER_UPDATE_BRANCH $DOCKER_UPDATE_BRANCH
cp -rp Dockerfile $DOCKER_UPDATE_BRANCH
pushd $DOCKER_UPDATE_BRANCH
git status
git diff Dockerfile
git add Dockerfile
git commit -m "update daaltk url" Dockerfile 
echo git push origin $BRANCH
git push origin $BRANCH
popd
