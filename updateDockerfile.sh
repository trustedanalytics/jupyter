#!/bin/bash
BRANCH=$1

chmod +x git-asset

DAALTK_URL=$(./git-asset -t $GIT_TOKEN -o trustedanalytics -r daal-tk download  --artifact-type daaltk-installer --release-type RC)
echo $DAALTK_URL
sed -i "s|ARG TKLIBS_INSTALLER_URL=.*|ARG TKLIBS_INSTALLER_URL=\"$DAALTK_URL\"|g" Dockerfile

git clone git@github.com:trustedanalytics/jupyter.git -b $BRANCH $BRANCH
cp -rp Dockerfile $BRANCH

pushd $BRANCH
git submodule update --init --recursive
git status

if [ -n "$(git status --porcelain)" ]; then 
  echo "local changes need to be pushed"
  git add Dockerfile
  git commit -m "update daaltk url" Dockerfile 
  echo git push origin $BRANCH
  git push origin $BRANCH
else 
  echo "no changes";
fi

popd
