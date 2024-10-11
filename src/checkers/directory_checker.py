from pathlib import Path
import logging
import json

import numpy as np
import xarray as xr

from checkers.checker_00_file_name import FileNameChecker
from checkers.checker_01_standard_compliance import StandardComplianceChecker
from checkers.checker_02_spatial_completeness import SpatialCompletenessChecker
from checkers.checker_03_spatial_consistency import SpatialConsistencyChecker
from checkers.checker_04_temporal_consistency import TemporalConsistencyChecker
from checkers.checker_05_valid_ranges import ValidRangesChecker
from checkers.checker_06_states_transitions import StatesTransitionsChecker

from utils.path_utils import get_file_type, get_activity_id, \
                             get_dataset_category, get_target_mip, \
                             get_source_id, get_grid_type, get_dates_range                          
from utils.log_utils import update_log_paths

class DirectoryChecker:

    def __init__(
        self, directory, log_path='logs', 
        base_path='', references=None,
        flag_spatial_completeness=True, 
        flag_spatial_consistency=True,
        flag_temporal_consistency=True,
        flag_valid_ranges=True, 
        flag_states_transitions=True, 
        required_file_types=[], required_variables={}, required_coords={}, 
        required_attributes=[], required_attributes_in_vars=[]
    ):

        # Set up basic logging
        logging.basicConfig(level='DEBUG')

        # Attributes defined in config
        self.directory = Path(directory)
        self.references = references
        self.reference_file = None 
        self.log_root_dir = Path(log_path)

        # Check directory existence
        assert self.directory.exists(), f"Directory {self.directory} not found"
        assert self.directory.is_dir(), f"{self.directory} is not a directory"

        self.variable = None
        self.required_variables_all = required_variables
        self.required_variables = [] 
        self.required_coords = required_coords
        self.required_attributes = required_attributes
        self.required_attributes_in_vars = required_attributes_in_vars
        self.required_file_types = required_file_types
        self.coordinate_list = None
        
        self.activity_id = None 
        self.dataset_category = None 
        self.target_mip = None 
        self.source_id = None 
        self.grid_type = None 

        self.expected_lon = []
        self.expected_lat = []

        self.re_pattern = None

        # Initialize other attributes
        self.file_counter = 0  # Number of files already checked
        self.boundaries = {} # Valid ranges boundaries for variable
        self.file = None  # Current file being checked
        self.file_type = None # Type of the file: "multiple-management", "multiple-states", "multiple-transitions"
        self.filename_firstpart = None
        self.ds = None  # Opened dataset of current file
        self.is_valid = None  # Flag validity of file name
        self.last_checked_file = None  # Name of previous file
        self.missing_value = None  # netCDF attribute missing_value
        self.fill_value = None  # netCDF attribute _FillValue
        self.date_range = None
        # self.calendar = None  # netCDF attribute time:calendar
        self.checker_results = {}  # Nested dictionary to store check results
        self.variable_list = {}
        self.varname = ''
        self.file_name_corrected = ''

        # Flags for individual checks
        self.flag_file_name = True
        self.flag_standard_compliance = True
        self.flag_spatial_completeness = flag_spatial_completeness
        self.flag_spatial_consistency = flag_spatial_consistency
        self.flag_temporal_consistency = flag_temporal_consistency
        self.flag_valid_ranges = flag_valid_ranges
        self.flag_states_transitions = flag_states_transitions
        
        self.base_path = base_path
        
    # Read variable information for landuse files
    def read_variable_info(self, file_path):
        """
        Read information about a variable from a json file
        """
       
        with open(file_path, 'r') as f:
            
            if self.data_source == 'landuse':   
                
                variables = json.load(f)[self.file_type]
            
                if list(variables.keys())==[]:
                    logging.info(
                        f"No valid ranges information for the file {self.file}"
                    )

                for var in self.required_variables: 
                    if var in list(variables.keys()):
                        
                        logging.info(
                            f"Reading {var} variable boundary information from src/variable-info_landuse.json: "
                            f"{variables[var]['boundaries']}"
                        )
                        self.boundaries[var] = variables[var]['boundaries']
                    else:
                        logging.info(
                            f"Valid range of variable {var} is unknown - please set it in src/variable-info_landuse.json"
                        )
                for var in list(variables.keys()):
                    if var not in self.required_variables:
                        logging.info(
                        f"Valid range of variable {var} is defined but the variable is not in the required variable list"
                    )
            
                                    
            # emissions
            else:
            
                if self.data_source == 'emissions':
                    var_em = self.file_type 
                    # We set the same boundaries for all gas species and name the variable 'var' in variable-info_emissions.json 
                    tempvarname_for_emissions = 'var'

                    variables = json.load(f)[var_em]
                    # logging.info(f"emission variables={variables}")
                    logging.info(
                        f"Reading {var_em} variable boundary information from variable-info_emissions.json: "
                        f"{variables[tempvarname_for_emissions]['boundaries']}"
                    )
                    
                    self.boundaries[var_em] = variables[tempvarname_for_emissions]['boundaries'] 
                    #logging.info(f"self.boundaries[var_em]={self.boundaries[var_em]}")
                else:
                    logging.error(f"Error: Wrong data_source: should be only 'landuse' or 'emissions'")
                    
        return       
    
    def read_reference(self, path):

        reference = None
        try:
            reference = xr.open_dataset(path)
        except:
            try:
                reference = xr.open_dataset(path, decode_times=False)
            except:
                logging.error(
                f"Reference file {path} is absent or can not be opened"
                ) 
                return None

        return reference


    def run_checker(self):
        
        # Set up logging directories
        update_log_paths(self.log_root_dir, self.directory)

        # Count files
        list_files = list(self.directory.iterdir())
        list_files.sort()
        n_files = len(list_files)

        for file in list_files:
            
            self.file = file
            
            self.file_name_corrected = file.name
            if '__' in self.file_name_corrected:
                self.file_name_corrected = self.file_name_corrected.replace('__','-')
            if '_off-' in self.file_name_corrected:
                self.file_name_corrected = self.file_name_corrected.replace('_off','-off')
            if '_on-' in self.file_name_corrected:
                self.file_name_corrected = self.file_name_corrected.replace('_on','-')
                
            
            self.file_counter += 1
            self.checker_results[file.name] = {}
            
            logging.error(
                f'\n\n------------------------------------------------------------------------------------------------------------------\n'
                f'      Checking file {self.file_counter}/{n_files}: {file.name}\n'
                f'      ------------------------------------------------------------------------------------------------------------------\n'
                f'\n\n'
                )

            file_extension = str(self.file)[-3:]
            if (file_extension != '.nc'):
                logging.error(
                    f'File {self.file} is not a NetCDF file. Skipping all tests on this file'
                )
            else:            
                
                # for landuse varname=''
                self.varname, self.file_type, self.filename_firstpart = get_file_type(self.file_name_corrected) 
                
                chk = FileNameChecker(self)
                chk.run_checker()
                self.checker_results[file.name] = {
                    **self.checker_results[file.name], **chk.results
                    }

                file_type_counter = self.checker_results[file.name]['file_name']
                if (not file_type_counter):
                    
                    if 'multiple' in self.file_type:
                        self.data_source = 'landuse'
                        self.required_variables = self.required_variables_all[self.file_type]
                        self.read_variable_info(
                            self.base_path + '/src/variable-info_landuse.json'
                        )
                    else:
                        self.data_source = 'emissions' 
                        self.required_variables = [self.filename_firstpart.replace('-','_')] #.split('-')[1:] #.replace('-','_')]
                        
                        #logging.info(f"self.required_variables: {self.required_variables}")
                        self.read_variable_info(
                            self.base_path + '/src/variable-info_emissions.json'
                        )   
                        
                    self.coordinate_list = self.required_coords[self.file_type] 
                        
                    self.activity_id = get_activity_id(self.file_name_corrected) 
                    self.dataset_category = get_dataset_category(self.file_name_corrected) 
                    self.target_mip = get_target_mip(self.file_name_corrected)  
                    self.source_id = get_source_id(self.file_name_corrected)  
                    self.grid_type = get_grid_type(self.file_name_corrected)  
                    self.date_range = get_dates_range(self.file_name_corrected) 
                        
                    self.reference_file = self.read_reference(self.references[self.file_type][0]) 
                            
                    if self.reference_file:
                        self.expected_lat = self.reference_file.lat.values
                        self.expected_lon = self.reference_file.lon.values
                        
                        
                    if self.is_valid: 
                            
                        try:
                            ds =xr.open_dataset(file.absolute())
                                    
                        except:
                            ds =xr.open_dataset(file.absolute(), decode_times=False)
                            ds['calendar'] = '365_day'
                            ds['_FillValue'] = 1e20
                                
                        with ds:
                                
                            # Store xarray dataset
                            self.ds = ds
                            self.variable_list = list(ds.variables.keys())
                            vars_to_remove = ['longitude', 'lon', 'lon_bnds', 'lon_bounds', \
                                            'latitude', 'lat', 'lat_bnds', 'lat_bounds', 'crs', 'calendar', \
                                            '_FillValue', 'missing_value', 'time', 'time_bnds', 'time_bounds', \
                                            'gas', 'sector', 'sector_bnds', 'sector_bounds', 'year', 'month', \
                                            'unit', 'method', 'level', 'level_bnds', 'bounds_lon', 'bounds_lat', 'bounds_time']
                            self.variable_list = [v for v in self.variable_list if v not in vars_to_remove]
                               
                            #logging.info(f"required_variables={self.required_variables}")
                            for var in self.required_variables:
                                
                                if var not in self.variable_list:
                                    logging.error(
                                        f"Missing compulsory variable {var} as indicated in config.json"
                                    )


                            if self.flag_standard_compliance:
                                logging.info(
                                    f"Check: standard compliance"
                                )
                                chk = StandardComplianceChecker(self)
                                chk.run_checker()
                                self.checker_results[file.name] = {
                                    **self.checker_results[file.name], **chk.results
                                    }

                            if self.flag_spatial_completeness:
                                logging.info(
                                    f"Check: spatial completeness"
                                )
                                chk = SpatialCompletenessChecker(self)
                                chk.run_checker()
                                self.checker_results[file.name] = {
                                    **self.checker_results[file.name], **chk.results
                                    }

                            if self.flag_spatial_consistency:
                                logging.info(
                                    f'Check: spatial consistency'
                                )
                                chk = SpatialConsistencyChecker(self)
                                chk.run_checker()
                                self.checker_results[file.name] = {
                                    **self.checker_results[file.name], **chk.results
                                    }

                            if self.flag_temporal_consistency:
                                logging.info(
                                    f'Check: temporal consistency'
                                )
                                chk = TemporalConsistencyChecker(self)
                                chk.run_checker()
                                self.checker_results[file.name] = {
                                    **self.checker_results[file.name], **chk.results
                                    }

                            if self.flag_valid_ranges:
                                logging.info(
                                    f'Check: valid ranges'
                                )
                                chk = ValidRangesChecker(self)
                                chk.run_checker()
                                self.checker_results[file.name] = {
                                    **self.checker_results[file.name], **chk.results
                                    }

                            if (self.data_source == 'landuse'):        
                                if self.flag_states_transitions:
                                    logging.info(
                                        f'Check for landuse: sum of the gross landuse transitions should match the difference in states between two consecutive years'
                                    )
                                    chk = StatesTransitionsChecker(self)
                                    chk.run_checker()
                                    self.checker_results[file.name] = {
                                        **self.checker_results[file.name], **chk.results
                                        }
                     
            # Track information
            self.last_checked_file = self.file

                            
