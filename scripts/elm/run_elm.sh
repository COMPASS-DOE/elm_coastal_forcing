

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

# Load modules
ml python/3.10
ml py-pip
ml netcdf-c
ml mpi/2021.13

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
singularity run elm_pflotran.sif

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
#  EXECUTE IMAGE FROM HOST 
#----------------------------------------------


cd elm

# Make temp dir
mkdir -p /tmp/overlay

# Make file overlay
# --size 1024
apptainer overlay create --writable-tmpfs ~/elm/elm_pflotran.img

# From Ben Sulman's OLMT coastal runs: Two-column marsh simulation:
# --overlay tmp/overlay \

apptainer exec \
  --writable-tmpfs \
  --pwd /tools/OLMT \
  --bind ~/elm/elmdata:/inputdata \
  --bind ~/elm/cases:/cases \
  --bind ~/elm/elmoutput:/output \
  --bind ~/elm/elmoutput:/tools/OLMT/temp \
  --bind ~/elm/olmt_scripts:/tools/OLMT/scripts \
  ~/elm/elm_pflotran_coastalmain_amd64.sif \
  bash -c '
  \
  metdir="/inputdata/atm/datm7/atm_forcing.datm7.GSWP3.0.5d.v2.c180716_PIE-Grid/cpl_bypass_full/"
  surf="/inputdata/plum_island/PIE_surfdata_threecell.nc"
  domain="/inputdata/plum_island/PIE_domain_threecell.nc"
  tide_forcing="/inputdata/plum_island/PIE_tide_forcing.nc"
  params="/inputdata/plum_island/parms_PIE"
  \
  python site_fullrun.py \
      --machine docker-scream \
      --site US-PLM1 \
      --sitegroup Wetland \
      --caseidprefix test_marsh \
      \
      --nyears_ad_spinup 100 \
      --nyears_final_spinup 100 \
      --tstep 1 \
      --nyears_transient 51 \
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



  # export PATH=/usr/local/bin:$PATH
  # export CC=/usr/local/bin/mpicc      # force C compiler
  # export MPICC=/usr/local/bin/mpicc   # sometimes honored by CIME


# For exploration 
apptainer shell \
  --pwd /tools/OLMT \
  --bind ~/elm/elmdata:/inputdata \
  --bind ~/elm/elmoutput:/output \
  --bind ~/elm/elmoutput:/tools/OLMT/temp\
  --bind ~/elm/cases:/cases \
  /home/flue473/elm/elm_pflotran_amd64.sif

vim runcase.py



# #-----------------------------------------------------
# #Start an interactive session with both data and output bound
# apptainer shell \
#   --pwd /tools/OLMT \
#   --bind ~/elm/elmdata:/inputdata \
#   --bind ~/elm/elmoutput:/output \
#   --bind ~/elm/elmoutput:/tools/OLMT/temp\
#   --bind ~/elm/cases:/cases \
#   /home/flue473/elm/elm_pflotran_amd64.sif


# cd /tools/OLMT

# # Command inside the docker
# metdir="/inputdata/atm/datm7/atm_forcing.datm7.GSWP3.0.5d.v2.c180716_PIE-Grid/cpl_bypass_full/"
# surf="/inputdata/plum_island/PIE_surfdata_threecell.nc"
# domain="/inputdata/plum_island/PIE_domain_threecell.nc"
# tide_forcing="/inputdata/plum_island/PIE_tide_forcing.nc"
# params="/inputdata/plum_island/parms_PIE"


# python site_fullrun.py \
#     --machine docker \
#     --site US-PLM1 \
#     --sitegroup Wetland \
#     --caseidprefix test_marsh \
#     \
#     --nyears_ad_spinup 100 \
#     --nyears_final_spinup 100 \
#     --tstep 1 \
#     --nyears_transient 51 \
#     --hist_nhtfrq_trans -1 \
#     --hist_mfilt_trans 8760 \
#     --hist_mfilt_spinup 0 \
#     --hist_nhtfrq_spinup 12 \
#     --cn_only \
#     --np 3 \
#     \
#     --cpl_bypass \
#     --no_dynroot \
#     --spinup_vars \
#     --nopointdata \
#     --gswp3 \
#     --marsh \
#     --nofire \
#     --nopftdyn \
#     \
#     --model_root /E3SM \
#     --caseroot /cases \
#     --ccsm_input /inputdata \
#     --runroot /output \
#     \
#     --mpilib openmpi \
#     --pio_version 2 \
#     \
#     --metdir "$metdir" \
#     --domainfile "$domain" \
#     --surffile "$surf" \
#     --tide_forcing_file "$tide_forcing" \
#     --parm_file "$params"





#  # 607 #if (caseroot == runroot):
#  # 608 #    casedir=caseroot+"/"+casename+'/case'
#  # 609 #    os.system('mkdir -p '+casedir)
#  # 610 #elif (caseroot != "./"):
#  # 611 if (caseroot != "./"):
#  # 612     casedir=os.path.abspath(caseroot+"/"+casename)
#  # 613 else:
#  # 614     casedir=os.path.abspath(casename)
#  # 615


# ##############################
# # Run from OLMT dir
# cd /home/$USER/OLMT
# # Uncommented lines 602-604
#   # --bind /home/flue473/E3SMv2/code/20210806:/model_root \


# # From Ben Sulman's OLMT coastal runs
# # Two-column marsh simulation:
# apptainer exec \
#   --bind ~/elm/elmdata:/inputdata \
#   --bind ~/elm/elmoutput:/output \
#   --bind ~/elm/cases:/cases \
#   --bind ~/OLMT:/OLMT \
#   /home/flue473/elm/elm_pflotran.sif \
#   bash -lc '
#   \
#   gmake() { make "$@"; }
#   export -f gmake
#   \
#   export PATH=$PATH:/usr/local/netcdf/bin:/usr/local/hdf5/bin:/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:
#   export PATH=$PATH:/msc/apps/compilers/oneapi/mpi/2021.13/bin
#   \
#   metdir="/inputdata/atm/datm7/atm_forcing.datm7.GSWP3.0.5d.v2.c180716_PIE-Grid/cpl_bypass_full/"
#   surf="/inputdata/plum_island/PIE_surfdata_threecell.nc"
#   domain="/inputdata/plum_island/PIE_domain_threecell.nc"
#   tide_forcing="/inputdata/plum_island/PIE_tide_forcing.nc"
#   params="/inputdata/plum_island/parms_PIE"
#   \
#   python ~/OLMT/site_fullrun.py \
#       --machine docker-scream \
#       --site US-PLM1 \
#       --sitegroup Wetland \
#       --caseidprefix test_marsh \
#       \
#       --nyears_ad_spinup 100 \
#       --nyears_final_spinup 100 \
#       --tstep 1 \
#       --nyears_transient 51 \
#       \
#       --cpl_bypass \
#       --no_dynroot \
#       --spinup_vars \
#       --nopointdata \
#       --gswp3 \
#       --marsh \
#       --nofire \
#       --nopftdyn \
#       \
#       --runroot /cases \
#       --model_root /E3SM \
#       --caseroot /cases \
#       --mpilib openmpi \
#       --pio_version 2 \
#       \
#       --ccsm_input /inputdata \
#       --metdir "$metdir" \
#       --domainfile "$domain" \
#       --surffile "$surf" \
#       --tide_forcing_file "$tide_forcing" \
#       --parm_file "$params"
#   '



# cd ~/elm/cases/cime_case_dirs

# # Find the case directory:
# ls cime_case_dirs
# # e.g. test_marsh_US-PLM1_ICB1850CNRDCTCBC_ad_spinup

# # Look at the GPTL build log:
# cat test_marsh_US-PLM1_ICB1850CNRDCTCBC_ad_spinup/bld/gptl.bldlog.* | sed -n '1,200p'
# cat test_marsh_US-PLM1_ICB1850CNRDCTCBC_ad_spinup/case_build.log | sed -n '1,200p'



#  -----INFO: using user-provided forcing data
# Under directory: /inputdata/atm/datm7/atm_forcing.datm7.GSWP3.0.5d.v2.c180716_PIE-Grid/cpl_bypass_full/
# clm_params_c180524.nc
# nccopy -3 /inputdata/lnd/clm2/paramdata/clm_params_c180524.nc /OLMT/temp/clm_params.nc
# Parameter humhol_ht not found in clm_params.nc. Adding.
# No PFT specified. Assuming universal parameter
# Parameter humhol_dist not found in clm_params.nc. Adding.
# No PFT specified. Assuming universal parameter
# Parameter hum_frac not found in clm_params.nc. Adding.
# No PFT specified. Assuming universal parameter
# Parameter tide_baseline not found in clm_params.nc. Adding.
# No PFT specified. Assuming universal parameter
# Parameter crit_gdd1 not found in clm_params.nc. Adding.
# PFT specified. Setting value for all PFTs
# Parameter crit_gdd2 not found in clm_params.nc. Adding.
# PFT specified. Setting value for all PFTs
# Parameter sal_opt not found in clm_params.nc. Adding.
# PFT specified. Setting value for all PFTs
# Parameter sal_tol not found in clm_params.nc. Adding.
# PFT specdified. Setting value for all PFTs
# Parameter sal_threshold not found in clm_params.nc. Adding.
# PFT specified. Setting value for all PFTs
# Parameter sfcflow_ratescale not found in clm_params.nc. Adding.
# No PFT specified. Assuming universal parameter
# Parameter qflx_h2osfc_surfrate not found in clm_params.nc. Adding.
# No PFT specified. Assuming universal parameter
# ./create_newcase --case /cases/cime_case_dirs/test_marsh_US-PLM1_ICB1850CNRDCTCBC_ad_spinup --mach docker-scream --compset ICB1850CNRDCTCBC --res ELM_USRDAT --mpilib openmpi --walltime 6:0:00 --handle-preexisting-dirs u --project e3sm > /cases/cime_case_dirs/create_newcase.log 2>&1
# test_marsh_US-PLM1_ICB1850CNRDCTCBC_ad_spinup created.  See create_newcase.log for details
# Setting NTASKS_ATM to 1
# Setting NTASKS_LND to 1
# Setting NTASKS_ICE to 1
# Setting NTASKS_OCN to 1
# Setting NTASKS_CPL to 1
# Setting NTASKS_GLC to 1
# Setting NTASKS_ROF to 1
# Setting NTASKS_WAV to 1
# Setting NTASKS_ESP to 1
# Setting NTASKS_IAC to 1
# Running case.setup
# Turning on MARSH modification

# ./xmlchange --append ELM_CONFIG_OPTS='-cppdefs " -DMODAL_AER -DMARSH"'
# Running case.build
# Building case in directory /cases/cime_case_dirs/test_marsh_US-PLM1_ICB1850CNRDCTCBC_ad_spinup
# sharedlib_only is False
# model_only is False
# Generating component namelists as part of build
#   2026-02-10 17:31:50 atm
# Create namelist for component satm
#    Calling /E3SM/components/stub_comps/satm/cime_config/buildnml
#   2026-02-10 17:31:50 lnd
# Create namelist for component elm
#    Calling /E3SM/components/elm/cime_config/buildnml
#   2026-02-10 17:31:50 ice
# Create namelist for component sice
#    Calling /E3SM/components/stub_comps/sice/cime_config/buildnml
#   2026-02-10 17:31:50 ocn
# Create namelist for component socn
#    Calling /E3SM/components/stub_comps/socn/cime_config/buildnml
#   2026-02-10 17:31:50 rof
# Create namelist for component mosart
#    Calling /E3SM/components/mosart//cime_config/buildnml
#   2026-02-10 17:31:50 glc
# Create namelist for component sglc
#    Calling /E3SM/components/stub_comps/sglc/cime_config/buildnml
#   2026-02-10 17:31:50 wav
# Create namelist for component swav
#    Calling /E3SM/components/stub_comps/swav/cime_config/buildnml
#   2026-02-10 17:31:50 iac
# Create namelist for component siac
#    Calling /E3SM/components/stub_comps/siac/cime_config/buildnml
#   2026-02-10 17:31:50 esp
# Create namelist for component sesp
#    Calling /E3SM/components/stub_comps/sesp/cime_config/buildnml
#   2026-02-10 17:31:50 cpl
# Create namelist for component drv
#    Calling /E3SM/driver-mct/cime_config/buildnml
# Building gptl with output to file /cases/test_marsh_US-PLM1_ICB1850CNRDCTCBC_ad_spinup/bld/gptl.bldlog.260210-173150
#    Calling /E3SM/share/build/buildlib.gptl
# ERROR: /E3SM/share/build/buildlib.gptl FAILED, cat /cases/test_marsh_US-PLM1_ICB1850CNRDCTCBC_ad_spinup/bld/gptl.bldlog.260210-173150
# Error:  Pointclm.py failed to build case.  Aborting
# See /cases/cime_case_dirs/test_marsh_US-PLM1_ICB1850CNRDCTCBC_ad_spinup/case_build.log for details
# Site_fullrun:  Error in runcase.py for ad_spinup



# #------------------------------------------------------
# # Set up github?


# # Check the SSH key 
# ssh -T git@github.com
# # Warning: Permanently added the ECDSA host key for IP address '140.82.114.4' to the list of known hosts.
# # git@github.com: Permission denied (publickey).