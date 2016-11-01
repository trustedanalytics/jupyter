#!/bin/bash

# Handle special flags if we're root
if [ $UID == 0 ] ; then
    # Change UID of NB_USER to NB_UID if it does not match
    if [ "$NB_UID" != $(id -u $NB_USER) ] ; then
        usermod -u $NB_UID $NB_USER
    fi

    # Enable sudo if requested
    if [ ! -z "$GRANT_SUDO" ]; then
        echo "$NB_USER ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/notebook
    fi

    # Fix the permissions for $NB_USER
    chown -R $NB_UID $CONDA_DIR /home/$NB_USER

    # Start the notebook server
    exec su $NB_USER -c "env PATH=$PATH jupyter notebook $*"
else
    # Fix the permissions for $NB_USER
    chown -R $NB_UID $CONDA_DIR /home/$NB_USER


    # Otherwise just exec the notebook
    exec jupyter notebook $*
fi
