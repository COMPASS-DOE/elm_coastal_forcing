

# Synoptic run 
# Latest run from B.Sulman


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


#-----------
apptainer exec \
  --no-home \
  --home / \
  --pwd /tools/OLMT \
  --env CONTAINER_HOSTNAME=docker \
  --writable-tmpfs \
  --bind ~/elm/elmdata/COMPASS_synoptic_sims:/inputdata \
  --bind ~/elm/elmdata/COMPASS_synoptic_sims/data:/forcingdata \
  --bind ~/elm/cases:/cases \
  --bind ~/elm/elmoutput:/output \
  --bind ~/elm/elmoutput:/tools/OLMT/temp \
  --bind ~/elm/olmt_scripts:/tools/OLMT/scripts \
  ~/elm/sandbox_elm \
  bash -c '
  \
  metdir="/inputdata/atm/datm7/atm_forcing.datm7.GSWP3.0.5d.v2.c180716_PIE-Grid/cpl_bypass_full/"
  surf="/forcingdata/COMPASS_surfdata_multicell_fdrain.nc"
  domain="/forcingdata/COMPASS_domain_multicell.nc"
  tide_forcing="/forcingdata/COMPASS_hydro_BC_multicell.nc"
  params="/inputdata/COMPASS_synoptic_sims/surface_data/COMPASS_parms"
  \
  python site_fullrun.py \
      --machine docker \
      --site US-GC3 \
      --sitegroup Wetland \
      --caseidprefix synoptic_hydro \
      \
      --nyears_ad_spinup 100 \
      --nyears_final_spinup 10 \
      --nyears_transient 151 \
      --tstep 1 \
      --walltime 30 \ 
      --np 21 \
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
      --trans_varlist "soil_O2,ZWT,TWS/SOILLIQ,SOILICE,H2OSOI,H2OSFC,QFLX_ADV,QDRAI,QDRAI_VR,QFLX_EVAP_TOT,QVEGT,watsat" \
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


# Transient run
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
  surf="/inputdata/COMPASS_synoptic_sims/COMPASS_surfdata_multicell_v01.nc"
  domain="/inputdata/COMPASS_synoptic_sims/COMPASS_domain_multicell_v01.nc"
  tide_forcing="/inputdata/COMPASS_synoptic_sims/COMPASS_hydro_BC_multicell_v01.nc"
  params="/inputdata/COMPASS_synoptic_sims/surface_data/COMPASS_parms"
  \
  python site_fullrun.py \
      --machine docker \
      --site US-GC3 \
      --sitegroup Wetland \
      --caseidprefix synoptic_hydro \
      \
       --tstep 1 \
       --nyears_transient 5 \
       --walltime 24 \
       --run_startyear 2020 \
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
      --trans_varlist "soil_O2,ZWT,TWS/SOILLIQ,SOILICE,H2OSOI,H2OSFC,QFLX_ADV,QDRAI,QDRAI_VR,QFLX_EVAP_TOT,QVEGT,watsat" \
      \
      --finidat /gpfs/wolf2/cades/cli185/scratch/b0u/COMPASS_synoptic_newforcing_US-GC3_ICB20TRCNRDCTCBC/run/COMPASS_synoptic_newforcing_US-GC3_ICB20TRCNRDCTCBC.elm.r.2010-01-01-00000.nc \                  
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



