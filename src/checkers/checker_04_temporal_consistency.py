import logging
from dateutil.relativedelta import relativedelta

import numpy as np

from utils.path_utils import get_dates_range
                            


class TemporalConsistencyChecker:
    """
    Check the timesteps 
    """

    def __init__(self, dschecker):

        self.file = dschecker.file
        self.directory = dschecker.directory
        self.ds = dschecker.ds
        self.data_source = dschecker.data_source
        self.re_pattern = dschecker.re_pattern
        self.date_range = dschecker.date_range

        # Check results
        self.results = {}

    def check_timestep_spacing(self, timesteps):
      
        # Only for landuse files
        if (self.data_source == 'landuse'):
            
            for i, timestep in enumerate(timesteps):
                    
                # Skip first timestep
                if i == 0:
                    previous_time = timestep
                    continue

                # Check timesteps 
                # i is the number of the timesteps in the file
                # time = "2020-01-01" [0], "2025-01-01" [1], "2030-01-01" [2], "2035-01-01" [3], "2040-01-01" [4],
                #        "2045-01-01" [5], "2050-01-01" [6], "2055-01-01" [7], "2060-01-01" [8], "2070-01-01" [9], 
                #        "2080-01-01" [10], "2090-01-01" [11], "2100-01-01" [12]
                # The 'time' array is replaced by the 'timestep' array:
                # timesteps = [50, 55, 60, 65, 70, 75, 80, 85, 90, 100, 110, 120, 130]
                # timediff is the difference between two consequtive timesteps: timediff = timesteps[i] - timesteps[i-1]
                # for i<=8 (before 2060), timediff should be 5 years, for other i timediff should be 10 years
                
                if i<=8:
                    timediff = 5
                else:
                    timediff = 10

                if previous_time + timediff != timestep:
                    self.results['timestep_spacing'] = 2
                    logging.error(
                        #f"Timesteps are not consistent: timestep[{i}]={timestep} but expected timestep[{i}]={previous_time+timediff}"
                        f"Timesteps are not consistent: time[{i}]-time[{i-1}]={timestep-previous_time} years but expected {timediff} years"
                    )
                else:
                    self.results['timestep_spacing'] = 0
                    
                    # Store previous datetime
                    previous_time = timestep

        # emissions
        else:
           
            for i, timestep in enumerate(timesteps):

                date_month = timestep

                # Skip first timestep
                if i == 0:
                    previous_time = date_month
                    continue

                if i not in [12,24,36,48,60,72,84,96,108]:
                    reld = relativedelta(months=1)
                    if previous_time + reld != date_month:
                        self.results['timestep_spacing'] = 2
                        logging.error(
                            f'Timesteps are not consistent: {previous_time} + {reld} = {previous_time + reld} vs {timestep}'
                        )
                else:

                
                    if i == 12:
                        reld = relativedelta(months=4*12+1)
                    else: 
                        reld = relativedelta(months=9*12+1)
 
                    reld = relativedelta(months=9*12+1)
                    
                    if previous_time + reld != date_month:
                        self.results['timestep_spacing'] = 2
                        logging.error(
                            f'Timesteps are not consistent: {previous_time} + {reld} = {previous_time + reld} vs {timestep}'
                        )

                # Store previous datetime
                previous_time = date_month
        

    def run_checker(self):
        """
        Run temporal consistency check
        """
    
        if 'time' in self.ds:
            if (self.data_source != 'landuse'):
                datetimeindex = self.ds.indexes['time'].to_datetimeindex()
                timesteps = datetimeindex.map(lambda x : x.replace(day=1))
                    
            else:
                timesteps = self.ds.time.values
                
        else:
            timesteps = [1]


        if len(timesteps) == 1:  # Skip for single timestep file
            self.results['timestep_spacing'] = -1

        else:
            self.results['timestep_spacing'] = 0
            self.check_timestep_spacing(timesteps)

      
