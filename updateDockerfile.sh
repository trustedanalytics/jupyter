#!/bin/bash
BRANCH=$(echo $BRANCH | sed -e "s|tags/||g")
chmod +x git-asset

DAALTK_URL=$(./git-asset -t $GIT_TOKEN -o trustedanalytics -r daal-tk download  --artifact-type daaltk-installer --release-type RC)
echo $DAALTK_URL


echo $DAALTK_URL
sed -i "s|ARG TKLIBS_INSTALLER_URL=.*|ARG TKLIBS_INSTALLER_URL=\"$DAALTK_URL\"|g" Dockerfile
git status

git diff Dockerfile

git commit -m "update sparktk build" Dockerfile 


if [ "$BRANCH" != "" ]; then

  echo git checkout -b $BRANCH
  git checkout -b $BRANCH 

  echo git push origin $BRANCH
  git push origin $BRANCH
fi
