

# E3SM quick start:
https://e3sm.org/model/running-e3sm/e3sm-quick-start/

#------------------------------------------------------
# Guide to running ELM on COMPASS HPC
#------------------------------------------------------

# SSH to server
ssh flue473@compass.pnl.gov

# Verify whether the SSH key is connected to account
ssh -T git@github.com

# The .sif file is located in /home/$USER/elm


# 3) Activate virtual env.
source ~/venvs/xr-env/bin/activate



#------------------------------------------------------
# Open the image; COMPASS NEEDS THE amd64 VERSION
cd ~/elm
singularity run elm_pflotran.sif
exit

#------------------------------------------------------
# Run the download script inside the container; binding elmdata 
#------------------------------------------------------

# Run the data-download script inside the container, binding elmdata
apptainer exec \
  --bind ~/elm/elmdata:/inputdata \
  elm_pflotran.sif \
  /scripts/download_elm_singlesite_forcing_data.sh


# # These are the files I found with:
#  find . -iname '*PIE*'


#------------------------------------------------------
#  COMPASS FORCINGS
#------------------------------------------------------

# run Ben Sulman's make compass from script
cd /home/flue473/COMPASS_synoptic_sims/scripts
python make_COMPASS_ELM_forcing.py


# Check the run case script
vim ~/OLMT/runcase.py


#----------------------------------------------
#  RUN FROM INSIDE CONTAINER
#----------------------------------------------

cd ~/elm/
singularity run --no-home  elm_pflotran.sif

#  GET NAMES OF MACHINES IN DOCKER 
cd /E3SM/cime/scripts
./query_config --machines docker
# Machines on host E3SM: docker, linux-generic
# Machines in both dockers E3SM: docker-scream, linux-generic

# Print config compiler
vim /E3SM/cime/scripts/query_config

vim /E3SM/cime_config/machines/config_compilers.xml

vim /E3SM/cime_config/machines/config_machines.xml


grep -n "docker-scream" /E3SM/cime_config/machines/config_compilers.xml


cd /tools/OLMT
vim site_fullrun.py

###############################

# ERROR:
# FileNotFoundError: [Errno 2] No such file or directory: b'/tools/OLMT/temp/clm_params.nc'




#----------------------------------------------
#  MAKE SANDBOX
#----------------------------------------------


mkdir -p ~/elm/sandbox_elm
apptainer build --sandbox ~/elm/sandbox_elm ~/elm/elm_pflotran_coastalmain_amd64.sif


#----------------------------------------------
#  EXECUTE IMAGE FROM HOST 
#----------------------------------------------

# Make temp dir
mkdir -p ~/elm/tmp/overlay

# Make file overlay
# --size 1024
apptainer overlay create --writable-tmpfs ~/elm/elm_pflotran.img

# From Ben Sulman's OLMT coastal runs: Two-column marsh simulation:
# --overlay tmp/overlay \
--home /home/modeluser \

  # ~/elm/elm_pflotran_coastalmain_amd64.sif \

# if home is not set to root; the CIME installation doesn't run inside the container

# Fakeroot: makes it look like root access in the container
# if home is set to root; MPI stops from running 
# mpirun has detected an attempt to run as root. Running as root is *strongly* discouraged
  # --fakeroot \

# Alternative fix: allow MPI to run as root inside the container
# --env OMPI_ALLOW_RUN_AS_ROOT=1 \
# --env OMPI_ALLOW_RUN_AS_ROOT_CONFIRM=1


apptainer exec \
  --no-home \
  --home / \
  --pwd /tools/OLMT \
  --env CONTAINER_HOSTNAME=docker \
  --writable-tmpfs \
  --bind ~/elm/elmdata:/inputdata \
  --bind ~/elm/cases:/cases \
  --bind ~/elm/elmoutput:/output \
  --bind ~/elm/elmoutput:/tools/OLMT/temp \
  --bind ~/elm/olmt_scripts:/tools/OLMT/scripts \
  ~/elm/sandbox_elm \
  bash -c '
  \
  metdir="/inputdata/atm/datm7/atm_forcing.datm7.GSWP3.0.5d.v2.c180716_PIE-Grid/cpl_bypass_full/"
  surf="/inputdata/plum_island/PIE_surfdata_threecell.nc"
  domain="/inputdata/plum_island/PIE_domain_threecell.nc"
  tide_forcing="/inputdata/plum_island/PIE_tide_forcing.nc"
  params="/inputdata/plum_island/parms_PIE"
  \
  python site_fullrun.py \
      --machine docker \
      --site US-PLM1 \
      --sitegroup Wetland \
      --caseidprefix test_marsh \
      \
      --nyears_ad_spinup 10 \
      --nyears_final_spinup 10 \
      --nyears_transient 5 \
      --tstep 1 \
      \
      --cpl_bypass \
      --no_dynroot \
      --spinup_vars \
      --nopointdata \
      --gswp3 \
      --marsh \
      --nofire \
      --nopftdyn \
      \
      --runroot /output \
      --model_root /E3SM \
      --caseroot /cases \
      --mpilib openmpi \
      --pio_version 2 \
      \
      --ccsm_input /inputdata \
      --metdir "$metdir" \
      --domainfile "$domain" \
      --surffile "$surf" \
      --tide_forcing_file "$tide_forcing" \
      --parm_file "$params"
    '


#%%------------------------------------------
# Updated run (02/23/2026)


# ELM Variable list for synoptic sites
# varlist="TOTVEGC,TOTSOMC,TOTLITC,SOIL1C_vr,SOIL2C_vr,SOIL3C_vr,SOIL4C_vr,LITR1C_vr,LITR2C_vr,LITR3C_vr,LEAFC,\
# soil_O2,HR,GPP,NEE,NPP,SMINN,SMINN_TO_PLANT,DIC_vr,SIC_vr,H2OSOI,H2OSFC,H2OSFC_TIDE,SOILLIQ,SOILICE,ZWT,QFLX_ADV,\
# QFLX_LAT_AQU,QFLX_EVAP_TOT,QVEGT,watsat,chem_dt,soil_salinity,soil_pH,DOC_vr,DIC_vr,DOC_RUNOFF,DIC_RUNOFF,SMIN_NO3_RUNOFF,\
# soil_sulfate,soil_sulfide,CH4_vr,CH4FLUX_ALQUIMIA,QDRAI,QDRAI_VR,TSOI,soil_Fe2,soil_FeOxide,soil_FeS,soil_acetate,\
# LWdown,PSurf,Qair,Rainf,SWdown,Tair,Wind"


# Added arguments 
# --walltime 24 --run_startyear 2020
# --np 21   #  Number of processors
# --no_submit \
      # --np 1 \


      # --run_startyear 2015 \

varlist="H2OSOI,H2OSFC,H2OSFC_TIDE,SOILLIQ,SOILICE,ZWT,QFLX_ADV,QFLX_LAT_AQU,QFLX_EVAP_TOT,QVEGT,watsat,soil_salinity,soil_pH,QDRAI,QDRAI_VR,TSOI"
      


apptainer exec \
  --no-home \
  --home / \
  --pwd /tools/OLMT \
  --env CONTAINER_HOSTNAME=docker \
  --writable-tmpfs \
  --bind ~/elm/elmdata:/inputdata \
  --bind ~/elm/cases:/cases \
  --bind ~/elm/elmoutput:/output \
  --bind ~/elm/elmoutput:/tools/OLMT/temp \
  --bind ~/elm/olmt_scripts:/tools/OLMT/scripts \
  ~/elm/sandbox_elm \
  bash -c '
  \
  metdir="/inputdata/atm/datm7/atm_forcing.datm7.GSWP3.0.5d.v2.c180716_PIE-Grid/cpl_bypass_full/"
  surf="/inputdata/plum_island/PIE_surfdata_threecell.nc"
  domain="/inputdata/plum_island/PIE_domain_threecell.nc"
  tide_forcing="/inputdata/plum_island/PIE_tide_forcing.nc"
  params="/inputdata/plum_island/parms_PIE" \
  varlist="ZWT"
  \
  python site_fullrun.py \
      --machine docker \
      --site US-PLM1 \
      --sitegroup Wetland \
      --caseidprefix test_marsh \
      \
      --nyears_ad_spinup 1 \
      --nyears_final_spinup 1 \
      --nyears_transient 1 \
      --tstep 1 \
      --hist_nhtfrq_trans -1 \
      \
      --cpl_bypass \
      --no_dynroot \
      --spinup_vars \
      --nopointdata \
      --gswp3 \
      --marsh \
      --nofire \
      --nopftdyn \
      \
      --runroot /output \
      --model_root /E3SM \
      --caseroot /cases \
      --mpilib openmpi \
      --pio_version 2 \
      \
      --ccsm_input /inputdata \
      --metdir "$metdir" \
      --domainfile "$domain" \
      --surffile "$surf" \
      --tide_forcing_file "$tide_forcing" \
      --parm_file "$params" \
      --hist_vars "$varlist"
    '
