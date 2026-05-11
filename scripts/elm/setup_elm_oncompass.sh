# setup_elm_oncompass.sh

#------------------------------------------------------
#  GLOSSARY
#------------------------------------------------------
# OLM: Offline Land Model Testbed
# CIME: Common Infrastructure for Modeling the Earth (handles things like: case creation, building and running the model managing input data, namelists, and configuration, coupling between model components)

#------------------------------------------------------
# COMMANDS
#------------------------------------------------------
# pwd  to print working directory
# ~/ is shortcut for home directory 
# To exit vim without saving  :qa  # or :q!
#               or write then quit  :wq
# To search in vim:    /  word  \>

# SIF = Simple Interaction File (networks, Cytoscape

#------------------------------------------------------
#  GITHUB KEY
#------------------------------------------------------

# Verify whether the SSH key is connected to account
ssh -T git@github.com

# # List SSH public keys
# ls ~/.ssh/*.pub

# To get permanent key, use this command instead of the one with ed25519 (that was changes)
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"
# eval "$(ssh-agent -s)"
# ssh-add ~/.ssh/id_ed25519   # or id_rsa


# If needed, pull the docker from DockerHub and convert it to a loccal Apptainer image file
apptainer pull elm_pflotran_amd64.sif docker://bsulman/elm_pflotran:elm_pflotran_amd64


#------------------------------------------------------
#  DOWNLOAD OTHER .SIF IMAGE
#------------------------------------------------------

# OR use elm_pflotran_coastalmain_amd64 ?
apptainer pull elm_pflotran_amd64.sif docker://bsulman/elm_pflotran:elm_pflotran_amd64
apptainer pull elm_pflotran_coastalmain_amd64.sif docker://bsulman/elm_pflotran_coastalmain_amd64



#------------------------------------------------------
#  ENV SET-UP
#------------------------------------------------------

# CompassHPC runs on python 3.9.5
# To load python 3.10.10 instead:
ml python/3.10
ml py-pip
# The docker runs on Python 3.7, and returns this message:
# Python 3.8 is recommended to run CIME. You have 3.7.

# 1) List venv environments
ls -1 ~/venvs

# 2) Create a venv in your home (one-time)
python3 -m venv ~/venvs/xr-env

# 3) Activate virtual env.
source ~/venvs/xr-env/bin/activate


# Install packages
python -m pip install --upgrade pip
python -m pip install xarray
python -m pip install matplotlib
python -m pip install netcdf4

#------------------------------------------------------
# COMMANDS
#------------------------------------------------------

# Get singularity version
singularity --version


#------------------------------------------------------
# First time set-up; copy template outside of image
#------------------------------------------------------

# Create directories on host to replace Docker volumes
mkdir -p /home/$USER/elm/elmscripts
mkdir -p /home/$USER/elm/elm/elmdata
mkdir -p /home/$USER/elm/elmoutput

# Start apptainer, with the new folder directory bound
apptainer shell \
  --bind /home/flue473/elm/elmscripts:/host_elm_scripts \
  elm_pflotran.sif

# Copy the file to the bound directory
cp /E3SM/run_e3sm.template.sh \
   /host_elm_scripts/run_e3sm.etiennetest.sh


#TODO: The template doc needs a machine name;
# Either use clogin1.compass.pnl.gov or clogin1 ???


#------------------------------------------------------
# Once inside the apptainer...

# Get top-level directories with sizes
du -h -d 1 / 2>/dev/null

# Navigate to right directory image
# because by default, wd is bound to host home dir: /home/flue473/elm
cd /E3SM

# Open the run/config file
vim run_e3sm.template.sh

# Run the E3SM set-up script
bash run_e3sm.template.sh

# This creates a directory /home/flue473/E3SMv2
# Delete it to prevent overwriting
rm -rf /home/flue473/E3SMv2

# To escape the Apptainer
exit


#------------------------------------------------------
# GET OLMT 
#------------------------------------------------------

# Clone OLMT
git clone git@github.com:dmricciuto/OLMT.git

cd OLMT

# Get Ben's OLMT version instead
git fetch origin
git branch -r | grep bsulman/coastal_main


#------------------------------------------------------
#  GET BEN'S SYNOPTIC SIMS FORCING REPO
#------------------------------------------------------
git clone git@github.com:bsulman/COMPASS_synoptic_sims.git


#------------------------------------------------------
#  RUN MODIFIED TEMPLATE
#------------------------------------------------------


mkdir -p /home/flue473/elm/cases
mkdir -p /home/flue473/elm/runs
mkdir -p /home/flue473/elm/archive


# Modify the template document:
# 1. Comment out the fetch_code  execution
# 2. Modify the computer name to "compy"
# 3. modify the CASEROOT
vim elmscripts/run_e3sm.etiennetest.sh


# If need to delete the case output folder if it already exists (won't overwrite)
rm -rf cases/tests/

# Run docker (from outside), running script to prepare d
apptainer exec \
  --bind /home/flue473/elm/elmdata:/inputdata \
  --bind /home/flue473/elm/elmscripts:/host_elm_scripts \
  --bind /home/flue473/elm/cases:/cases \
  --bind /home/flue473/elm/runs:/runs \
  --bind /home/flue473/elm/archive:/archive \
  elm_pflotran.sif \
  /host_elm_scripts/run_e3sm.etiennetest.sh

#!ERROR: inputdata root is not a directory or is not readable: /compyfs/inputdata

