#!/bin/bash

###
### How to use the installation script
### ===================================
#
# To install this package, you need conda installed (the conda command must work
# in your shell, see https://docs.conda.io/en/latest/miniconda.html),
# then install the package like:
#
#   $ bash install.sh -d --python 3.6 --name *env_name*
#
# To get information on the flags, run
#
#   $ bash install.sh --help"
###

function setup()
 {
  local __py_vers=$1
  local __name=$2
  local __develop=$3

  conda config --set always_yes yes
  conda create -n $__name python=$__py_vers
  conda activate $__name
  conda env update -f environment.yml -n $__name

  if [[ $__develop -eq 0 ]]; then
    echo "Installing package..."
    python setup.py install
  else
    echo "Installing package in development mode..."
    python setup.py develop
  fi;

 conda config --set always_yes no
 }

function install()
  {
  local __name=$NAME
  local __py=$PYTHON
  local __develop=$DEVELOP

  conda_base=$(conda info --base)
  source $conda_base/etc/profile.d/conda.sh

  echo "Setup environment $__name ..."
  setup $__py $__name $__develop
  }

#===============================================================================

# default
DEVELOP=0
NAME="ecmwf_models"
PYTHON="3.6"
_help=0

# Loop through arguments and process them
for arg in "$@"
do
    case $arg in
        -d) #switch
        DEVELOP=1
        shift # Remove --develop from processing
        ;;
        -n|--name) # kwarg
        NAME="$2"
        shift # Remove argument name from processing
        shift # Remove argument value from processing
        ;;
        -p|--python) # kwarg
        PYTHON="$2"
        shift # Remove argument name from processing
        shift # Remove argument value from processing
        ;;
        -h|--help)
        _help=1
        shift
        echo "Usage: bash install.sh [OPTION] "
        echo "Setup environment for developing this package. "
        echo "Optional arguments/flags to pass to >> $ bash install.sh "
        echo "-d                 Flag to install package in development mode (default: False) "
        echo "-n, --name         Name of the environment to install, (default: $NAME)"
        echo "-p, --python       Python version to install together with other dependencies (default: $PYTHON) "
        echo "-h, --help         Show this help message."
    esac
done

if [[ $_help -eq 0 ]]; then
  install $NAME $PYTHON $DEVELOP;
  echo " "
  echo "Installation complete."
  echo " "
  echo "#"
  echo "# To activate this environment, use"
  echo "#"
  echo "#   $ conda activate $NAME"
  echo "#"
  echo "# To deactivate an active environment, use"
  echo "#"
  echo "#   $ conda deactivate $NAME"
  echo " "
fi

