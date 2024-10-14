

## Requirements
The data checker relies on the following libraries:

numpy, xarray, argparse, dateutil.relativedelta, datetime, json, sys, os, pathlib, re, stat, logging, typing

Install requirements with:

`pip install numpy xarray python-dateutil`

## How to run

1. Add `${checkerdir}/src` to `PYTHONPATH` in `~/.bashrc`, where `${checkerdir}` is the full path to the checker directory:<br>
`export PYTHONPATH="${PYTHONPATH}:${checkerdir}/src"`

<br>

2. Configure the config file (`config_lu.json` for landuse or `config_em.json` for emissions), which contains the following settings:
   - `directory`: the directory with the files requiring checking;
   - `log_path`: where to save logs (relative path inside the checker directory);
   - `base_path`: full path to the checker directory;
   - `required_file_types`: for the landuse files there are "multiple-management", "multiple-states", "multiple-transitions";
   - `required_variables`: variables which are mandatory to be in the files (for each file type independently)
   - `required_coords`: coordinates which are mandatory to be in the files (for each file type independently);
   - `required_attributes`: general attributes which are mandatory for the files;
   - `required_attributes_in_vars`: variable-specific attributes which are mandatory for the files.

<br>

3. Configure the file `${checkerdir}/src/variable-info_landuse.json` or `${checkerdir}/src/variable-info_emissions.json` which contains the variable ranges requirements (for each file type independently).
<br>

4. Run: `python run_script.py config_lu.json` or `python run_script.py config_em.json`. 

## Checkers 

**FileNameChecker**: `${checkerdir}/src/checkers/checker_00_file_name.py`
 
Check filetype ("multiple-management", "multiple-states", or "multiple-transitions") and the filename (it should match a pattern `multiple-<...>_input4MIPs_landState_<...>_gn_YYYY-YYYY.nc`). 
It uses functions from `${checkerdir}/src/utils/misc_utils.py`.
<br>

**StandardComplianceChecker**: `${checkerdir}/src/checkers/checker_01_standard_compliance.py`

Check file permissions, dimension variables, compulsory attributes, `_FillValue`.
<br>  

**SpatialCompletenessChecker**: `${checkerdir}/src/checkers/checker_02_spatial_completeness.py`

Create the reference mask based on the reference file and check the presence of missing values. 
It uses functions from `${checkerdir}/src/utils/misc_utils.py`.
<br>

**SpatialConsistencyChecker**: `${checkerdir}/src/checkers/checker_03_spatial_consistency.py`

Check that the lon/lat grid points correspond to the reference file.
<br>

**TemporalConsistencyChecker**: `${checkerdir}/src/checkers/checker_04_temporal_consistency.py`

Check timesteps for consistency.
It uses functions from `${checkerdir}/src/utils/path_utils.py`.

`i` is the number of the timestep in the file:<br>
`time` = "2020-01-01" [0], "2025-01-01" [1], "2030-01-01" [2], "2035-01-01" [3], "2040-01-01" [4],
        "2045-01-01" [5], "2050-01-01" [6], "2055-01-01" [7], "2060-01-01" [8], "2070-01-01" [9], 
        "2080-01-01" [10], "2090-01-01" [11], "2100-01-01" [12]<br>

During the check, the 'time' array is replaced by the 'timestep' array:<br>
`timesteps` = [50, 55, 60, 65, 70, 75, 80, 85, 90, 100, 110, 120, 130]<br>
               
`timediff` is the difference between two consequtive timesteps: `timediff = timesteps[i] - timesteps[i-1]`.<br> 
Here we have `timefiff` of either 5 or 10 years:<br>
- for `i`<=8 (before 2060) `timediff` should be 5 years
- for other `i` (after 2060) `timediff` should be 10 years

<br>

**ValidRangesChecker**: `${checkerdir}/src/checkers/checker_05_valid_ranges.py`

Check that data values are in the required range (defined in `${checkerdir}/src/variable-info.json`).
It uses functions from `${checkerdir}/src/utils/misc_utils.py`.


**StatesTransitionsChecker**: `${checkerdir}/src/checkers/checker_06_states_transitions.py`

1. For each `multiple-states_<XXX>`: check that the sum of all variables is close to 1.

2. For each `multiple-transitions_<XXX>`: take the corresponding file `multiple-states_<XXX>` (with the same `<XXX>`) and check that the sum of the gross landuse transitions matches the difference in states between two consecutive years (except for the variables `secdf, primf, secdn, primn`).

Algorithm for `(2)`: 

- In `multiple-states_<...>`, we have variables `'c3ann' 'c3nfx' 'c3per' ...` , so for each variable `var` we take its value for the year Y: `var_states_Y`, and its value for the year Y+1: `var_states_(Y+1)`.
   
- In `multiple-transitions_<...>`, we have `'c3ann_to_c3nfx' 'c3ann_to_c3per' 'c3ann_to_c4ann' ...` , i.e. `X_to_var` and `var_to_X` with `var` from `multiple-states_<...>`.<br>
We calculate (for every year Y):<br>
`sum(X_to_var)` - the sum of all variables in `multiple-transitions_<...>` for the year Y with names `to_{var}`, and<br>
`sum(var_to_X)` - the sum of all variables in `multiple-transitions_<...>` for the year Y with names `{var}_to`,<br>
e.g. for `c3ann` at the year Y:<br>
`sum(X_to_var) = sum ['c3nfx_to_c3ann', 'c3per_to_c3ann', 'c4ann_to_c3ann', 'c4per_to_c3ann', 'primf_to_c3ann', 'primn_to_c3ann', 'secdf_to_c3ann', 'secdn_to_c3ann', 'urban_to_c3ann', 'pastr_to_c3ann', 'range_to_c3ann']`<br>
`sum(var_to_X) = sum ['c3ann_to_c3nfx', 'c3ann_to_c3per', 'c3ann_to_c4ann', 'c3ann_to_c4per', 'c3ann_to_secdf', 'c3ann_to_secdn', 'c3ann_to_urban', 'c3ann_to_pastr', 'c3ann_to_range']`


- We want this equation to be true:<br> 
`sum(X_to_var) - sum(var_to_X) = var_states_(Y+1) - var_states_Y`, <br>
so for each variable we calculate `delta` which should be close to 0:<br>
`delta = [ sum(X_to_var) - sum(var_to_X) ] - [ states_(Y+1) - states_Y) ]`



## Other files

- `${checkerdir}/run_script.py`:  run the "main" function; `${checkerdir}/src/checkers/directory_checker.py` and `${checkerdir}/scripts/check_file.py`: configure the parameters and run all checkers;
- `${checkerdir}/src/utils`: functions which are used by checkers.

## Logging

For each run, the checker creates a new logging directory (its name includes the dataset name, current date and time) in  `${checkerdir}/logs` (the "logs" name can be modified in `config_lu.json` in "log_path"). 

There are files: 
- `<...>_errors.log` - only errors;
- `<...>_output.log` - all information about the checking.