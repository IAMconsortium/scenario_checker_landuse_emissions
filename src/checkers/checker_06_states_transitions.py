import logging
import numpy as np
import xarray as xr
import os.path


class StatesTransitionsChecker:
   
    def __init__(self, dschecker):

        self.file = dschecker.file
        self.file_type = dschecker.file_type
        self.directory = dschecker.directory
        self.ds = dschecker.ds

        self.results = {}
       


    # check No 1: only for states - sum of all vars should be equal to 1
    # "states" is the file corresponding to the transition file self.file
    def check_sum_of_all_vars(self, states, vars_to_remove):
    
        vars_states = list(states.keys())
        vars_to_check = [v for v in vars_states if v not in vars_to_remove]
        
        N = len(states['time'].values)
        
        for t in range(N - 1):
        
            summ = 0
            for key in vars_to_check:
                summ += states[key].isel(time=t).values
        
            absmaxsum = np.nanmax(abs(summ))

            logging.info(
                f"        sum at timestep {t}: max={absmaxsum}"
            )
            if abs(absmaxsum - 1) > 1e-3:
                logging.warning(
                    f"        Error at timestep {t}"
                )
            

            '''
            if (t==1156):
                lat =  states[key].lat.values
                lon =  states[key].lon.values                         
                sum_da = xr.DataArray(sum,dims=["lat","lon"],coords=[('lat', lat),('lon', lon)])
                sum_da.name  = 'sum'
                sum_da.to_netcdf(f"{outdir}/sum_{t}.nc")
            '''



    # check No 2: the sum of the gross landuse transitions should be equal to the difference in states between two consecutive years 
    # this is ok for the reference files but delta is (sometimes?) not close to 0 for the forcings files

    def check_states_vs_transitions(self, trans, states, vars_to_remove):

        N = len(states['time'].values)

        vars_trans = list(trans.keys())
        vars_states = list(states.keys())

        vars_to_check = [v for v in vars_states if v not in vars_to_remove]

        for var in vars_to_check:
        

            X_to_var = "_to_"+var 
            var_to_X = var+"_to_" 
                
            logging.info(
                f"    Checking states vs transitions: delta = sum_{var}_transitions - states | Y - (Y+1))"
            )
            
            trans_X_to_var = [v for v in vars_trans if X_to_var in v] 
            trans_var_to_X = [v for v in vars_trans if var_to_X in v]
            
            for t in range(N - 1):
            
                sum_X_to_var = sum(trans[key].isel(time=t).values for key in trans_X_to_var)
                sum_var_to_X = sum(trans[key].isel(time=t).values for key in trans_var_to_X)
                
                thisyear = states[var].isel(time=t).values
                
                # this is just in case if we want to select either 
                # 1. this year and the next year, or 
                # 2. this year and the previous year 
                # yeartocheck = t+1 or t-1 
                # we selected t+1 based on the tests with the historical files 
                yeartocheck = t+1
                
                anotheryear = states[var].isel(time=yeartocheck).values

                result1 = sum_var_to_X - sum_X_to_var
                result2 = thisyear - anotheryear
                delta = result1 - result2
                
                '''
                lat, lon = states[var].lat.values, states[var].lon.values

                delta_da = xr.DataArray(delta, dims=["lat", "lon"], coords=[('lat', lat), ('lon', lon)])
                delta_da.name = f'{var}_to_X-X_to_{var} - states_this_yr-next_yr'
                delta_da.to_netcdf(f"{outdir}/delta_{var}_{t}.nc")
                '''

                if np.nanmax(abs(delta)) > 1e-5:
                    logging.warning(
                        f"        Warning: maxdelta for var {var} at timestep {t}: {np.nanmax(abs(delta))}"
                    )
                else:
                    logging.info(
                        f"        Correct: maxdelta for var {var} at timestep {t}: {np.nanmax(abs(delta))}"
                    )



    # run the checks 

    def run_checker(self):
        """
        Run valid ranges check
        """
       

        vars_to_remove_1 = ['longitude', 'lon', 'lon_bnds', 'lon_bounds', 
                        'latitude', 'lat', 'lat_bnds', 'lat_bounds', 'crs', 'calendar', 
                        '_FillValue', 'missing_value', 'time', 'time_bnds', 'time_bounds', 
                        'gas', 'sector', 'sector_bnds', 'sector_bounds', 'year', 'month', 
                        'unit', 'method', 'level', 'level_bnds', 'bounds_lon', 'bounds_lat', 'bounds_time', 
                        'secma', 'secmb']
        vars_to_remove_2 = vars_to_remove_1 + ['secdf', 'primf', 'secdn', 'primn']


        if self.file_type == "multiple-transitions":
            file_transitions = self.file.name
            logging.info(
                f"This is a multiple-transitions file. Checking that the sum of the gross landuse transitions "
                f"should be equal to the difference in states between two consecutive years"
            )

            tail = file_transitions[20:]
            file_states = "multiple-states" + tail   
             
            if not os.path.isfile(str(self.directory) + "/" + file_states):
                logging.error(
                    f'    No file corresponding to {file_transitions}! Skipping the check'
                )

            else:

                trans = self.ds
                states = xr.open_dataset(os.path.join(self.directory, file_states), decode_times=False)
                self.check_states_vs_transitions(trans, states, vars_to_remove_2)


        else:

            if self.file_type == "multiple-states":
                logging.info(
                    f"This is a multiple-states file. Checking that the sum of all variables should be close to 1"
                )
                states = self.ds 
               
                self.check_sum_of_all_vars(states, vars_to_remove_1)

            else:
                logging.info(
                    f"This file is neither multiple-states nor multiple-transitions. No additional check will be done"
                )
            
    
        
        

