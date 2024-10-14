import logging
import numpy as np
from utils.misc_utils import get_valid_data


class ValidRangesChecker:
    """
    Check that data values are in a given range 
    """

    def __init__(self, dschecker):

        self.file = dschecker.file
        self.file_type = dschecker.file_type
        self.data_source = dschecker.data_source
        self.directory = dschecker.directory
        self.ds = dschecker.ds
        self.variable = dschecker.variable
        self.variable_list = dschecker.variable_list 
        self.boundaries = dschecker.boundaries
        self.variable = dschecker.variable
        self.reference_file = dschecker.reference_file

        self.results = {}

    def check_allowed_values(self, min_value, max_value, var):
       
        logging.info(
            f'Found variable {var} '
        )

        data_array = self.ds[var]

        self.results['boundaries_min'] = 0
        self.results['boundaries_max'] = 0

        if 'time' in list(data_array.dims): 
            
            # counter to show the number of the timestep
            tt_ind=0

            for tt, data_at_timestep in data_array.groupby('time'):

                self.results['boundaries_min'] = 0
                self.results['boundaries_max'] = 0
                data = data_at_timestep.values
               
                data_min = np.nanmin(data)
                data_max = np.nanmax(data)
                if min_value is not None:

                    # a special case when we want to see if there are negative values
                    if min_value == 0: 
                        if (data_min < min_value):
                            self.results['boundaries_min'] = -1
                    
                    else:
                        if (data_min < min_value) and (not np.isclose(data_min, min_value, atol = 0.0001, rtol = 0.0001)):
                            self.results['boundaries_min'] = -1

                if max_value is not None:
                    if (data_max > max_value) and (not np.isclose(data_max, max_value, rtol = 0.0001)):
                        self.results['boundaries_max'] = 1
                

                if (self.results['boundaries_max'] != 0):
                    logging.error(
                        f'Invalid values of {var} '
                        f'in file {self.file.name} at t={tt_ind}: '
                        f'data_max = {data_max:.2e} > required max = {max_value}'
                    )
                if (self.results['boundaries_min'] != 0):
                    logging.error(
                        f'Invalid values of {var} '
                        f'in file {self.file.name} at t={tt_ind}: '
                        f'data_min = {data_min:.2e} < required min = {min_value}'
                    ) 
                
                if (self.results['boundaries_max'] == 0 and self.results['boundaries_min'] == 0):
                    logging.info(
                        f'   Correct values of {var} at t={tt_ind}'
                    )

                tt_ind = tt_ind + 1 
                        
        else:

            data = data_array.values
            data_min = np.nanmin(data)
            data_max = np.nanmax(data)

            if min_value is not None:
                if (data_min < min_value) and (not np.isclose(data_min, min_value, rtol = 0.0001)):
                    self.results['boundaries_min'] = -1
                    
            if max_value is not None:
                if (data_max > max_value) and (not np.isclose(data_max, max_value, rtol = 0.0001)):
                    self.results['boundaries_max'] = 1

           
            if (self.results['boundaries_max'] != 0):
                logging.error(
                    f'Invalid values of {var} '
                    f'in file {self.file.name}: data_max = {data_max:.2e} > required max = {max_value}'
                    )
            if (self.results['boundaries_min'] != 0):
                logging.error(
                    f'Invalid values of {var} '
                    f'in file {self.file.name}: data_min = {data_min:.2e} < required min = {min_value}') 
            if (self.results['boundaries_max'] == 0 and self.results['boundaries_min'] == 0):
                logging.info(
                    f'   Correct values of {var}'
                )
            

    def run_checker(self):
        """
        Run valid ranges check
        """
       
        if self.boundaries is None:
            self.results['boundaries_max'] = 2
            self.results['boundaries_min'] = -2
            logging.info(
                f'No boundaries to check for variable {self.variable}'
            )

        else:

            for var in self.variable_list:
                if var in self.boundaries:
                    min_allowed, max_allowed = self.boundaries[var]
                    self.check_allowed_values(min_allowed, max_allowed, var)
                else:
                    if self.data_source == "emissions":
                        # var_em is e.g. "em-anthro"
                        if self.file_type in self.boundaries:
                            var_em = self.file_type
                            min_allowed, max_allowed = self.boundaries[var_em]
                            
                        else:
                            logging.warning(
                                f'No valid ranges information for variable {var}'
                            )

    