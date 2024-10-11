import logging
from pathlib import Path
from stat import filemode
import json

class StandardComplianceChecker:
    """
    Check file permissions, dimension variables, compulsory attributes, _FillValue
    """

    NETCDF_MISSING_VALUES = {
            '_FillValue': 'fill_value'}
            #'missing_value': 'missing_value'}

    def __init__(self, dschecker):
        self.dschecker = dschecker

        self.file = dschecker.file
        self.data_source = dschecker.data_source 
        self.ds = dschecker.ds
        self.variable_list = dschecker.variable_list
        self.coordinate_list = dschecker.coordinate_list
        self.required_attributes = dschecker.required_attributes
        self.required_attributes_in_vars = dschecker.required_attributes_in_vars
        self.reference_file = dschecker.reference_file
        self.varname = dschecker.varname

        # Check results
        self.results = {}

    def check_unix_permissions(self):
        """
        Check that the user has at least read permissions for a given file
        """
        self.results['permissions'] = 0

        unix_filemode = filemode(Path(self.file).stat().st_mode)

        # unix_filemode[4] for group read permissions
        if (unix_filemode[7] != 'r') and (unix_filemode[4] != 'r'):
            self.results['permissions'] = 1
            logging.error(
                f'Wrong permissions. File {self.file.name} should be readable by the user'
            )

    def check_variable_name(self):
        """
        Check that file contains the data variable specified in the file name - only for emissions.
        Ignoring this for landuse
        """
        self.results['variable_name'] = 0

        if (self.data_source == "landuse"):
            self.results['variable_name'] = 1
            logging.info(
                f'This is a landuse file: search for the variable name in the file name not possible'
            )
           
        else:
            var = self.varname
            if (var not in self.ds.data_vars):
                self.results['variable_name'] = 1
                logging.warning(
                    f'Variable {var} is expected but not found'
                )
            else:
                logging.info(
                    f'Variable {var} found'
                )
        


    def check_dimension_names(self):
        """
        Check that required dimension variables and the compulsory attributes are present.
        """

        dimensions = self.coordinate_list    
      
        for dim in dimensions: 
            self.results[dim] = 0
           
            if not hasattr(self.ds, dim):
                self.results[dim] = 1
                logging.error(f'Missing compulsory dimension {dim} as indicated in config.json '
                              f'(please check also: lat vs latitude, lon vs longitude, etc)')
                
        attributes = self.required_attributes

        for attr in attributes:
            self.results[attr] = 0
            if not hasattr(self.ds, attr):
                self.results[attr] = 1
                logging.error(f'Missing compulsory attribute {attr} as indicated in config.json')
        
        attributes_in_vars = self.required_attributes_in_vars
        
        vars_to_remove = ['longitude', 'lon', 'lon_bnds', 'lon_bounds', 'latitude', 'lat', 'lat_bnds', 'lat_bounds', 'crs', 'calendar', \
                        '_FillValue', 'missing_value', 'time', 'time_bnds', 'gas', 'sector', 'sector_bnds', 'year', 'month', 'unit', 'method', \
                        'level', 'level_bnds', 'bounds_lon', 'bounds_lat', 'bounds_time']
        
        vars_to_check = [v for v in self.ds.keys() if v not in vars_to_remove]
        
        for attr_var in attributes_in_vars:
            self.results[attr_var] = 0

            for var in vars_to_check: 

                if not hasattr(self.ds[var], attr_var):
                    self.results[attr_var] = 1
                    logging.error(f'Variable {var} missing compulsory attribute {attr_var} as indicated in config.json')

                
    def check_missing_and_fill_value(self):
        """
        Check that netCDF attributes missing_value and _FillValue are present 
        and that they have the same values for all files
        """
        for netcdf_key, attr in self.NETCDF_MISSING_VALUES.items():  
            self.results[attr] = 0
            
            for var in self.variable_list: 
                
                try:
                    value = self.ds[var].encoding[netcdf_key] # value = 1e+20 
                    reference_value = getattr(self.dschecker, attr) 

                    if reference_value is not None:

                        TOLERANCE = 1.0e-5
                        if abs(value - reference_value) > TOLERANCE:
                            self.results[attr] = 1
                            logging.error(
                                f'Inconsistent value for netcdf key {netcdf_key}: {value}.'
                            )

                    else: 
                        setattr(self.dschecker, attr, value) 
                        
                except KeyError:
                    self.results[attr] = 2
                    logging.warning(
                        f'Missing netCDF key {netcdf_key} in file {self.file.name}'
                    )
    
    
    def run_checker(self):
        """
        Run standard compliance check
        """
        self.check_unix_permissions()
        self.check_variable_name()
        self.check_dimension_names()

        
        if self.results['variable_name'] != 0:
            self.results['missing_value'] = -1  # Can't be checked
            self.results['fill_value'] = -1  # Can't be checked

        else:
            self.check_missing_and_fill_value()


