import logging, os
import numpy as np
import xarray as xr
import warnings
warnings.filterwarnings("ignore")


from utils.misc_utils import get_valid_data #, get_invalid_data


class SpatialCompletenessChecker:
    """
    Check missing data values based on the mask
    """

    def __init__(self, dschecker):
        self.dschecker = dschecker

        self.ds = dschecker.ds
        self.file = dschecker.file
        self.data_source = dschecker.data_source
        self.variable = dschecker.variable
        self.variable_list = dschecker.variable_list
        self.reference_file = dschecker.reference_file
        self.filename_firstpart = dschecker.filename_firstpart

        # Check results
        self.results = {}


    def run_checker(self):
        """
        Run spatial completeness check
        """
        
        for var in self.variable_list:
            
            logging.info(
                f'Spatial completeness: checking {var} variable'
            ) 
            
            
            self.results['spatial_completeness'] = []
            timesteps_err = []
           
            if 'time' in list(self.ds.dims): 
               
                data_array = self.ds[var]

                try:
                    tt = data_array.time.values # for the reference files
                except:
                    tt = self.ds.time # for the forcing landuse files
    
                for i in range(len(tt)):
                    
                    data = data_array.isel(time=i).values
                    
                    if self.data_source == 'landuse':
                       
                        # For each var, take the reference mask (i.e. from the reference file) for the same var.
                        # If the reference mask for this var does not exist (i.e. this var is not in the reference file),
                        # then take the mask from another var in the reference file 
                        # as we suppose that the reference mask is same for all vars
                        if var in self.reference_file:
                            mask = np.isnan(self.reference_file[var].isel(time=1).values).astype(int)
                            if (i==0):
                                logging.info(
                                    f"    Mask is taken from the reference file for var={var}"
                                )
                            
                            
                            # This is for saving masks 
                            # Delete later if not needed
                            # ---- start
                            '''
                            mask_dir = f"mask_dir/{self.file.name}"
                            if not os.path.exists(mask_dir):
                                os.makedirs(mask_dir)

                            lat_nans =  data_array.lat.values
                            lon_nans =  data_array.lon.values                         
                            mask_da = xr.DataArray(mask,dims=["lat","lon"],coords=[('lat', lat_nans),('lon', lon_nans)])
                            mask_da.name = 'mask'
                            encoding = {'mask': {'_FillValue': 1.}}       
                            mask_da.to_netcdf(f"{mask_dir}/mask_{i}.nc",encoding=encoding)
                            '''
                            # ---- end
                                
                        else:
                            vars_from_reference = list(self.reference_file.variables.keys())
                            vars_to_remove = ['longitude', 'lon', 'lon_bnds', 'latitude', 'lat', 'lat_bnds', 'crs', 'calendar', \
                                                  '_FillValue', 'missing_value', 'time', 'time_bnds', 'gas', 'sector', 'sector_bnds', 'year', 'month', 'unit', 'method', \
                                                    'level', 'level_bnds', 'bounds_lon', 'bounds_lat', 'bounds_time']
                            vars_from_reference = [v for v in vars_from_reference if v not in vars_to_remove]
                            first_var = vars_from_reference[0]
                            mask = np.isnan(self.reference_file[first_var].isel(time=0).values) 
                            logging.info(
                                f"No reference mask for {var}, mask is taken from the reference mask for {first_var}"
                            )
                            
                        valid_data = get_valid_data(data, mask)

                        # Here the mask is taken from the same file which is being checked, not from the reference file
                        # Delete later if not needed
                        # ---- start
                        '''
                        mask = np.isnan(data_array.isel(time=0).values) 
                        print(f'Mask is taken from {var} at t=0')
                        valid_data = get_valid_data(data, mask)
                        '''
                        # ---- end
                        
                    # emissions
                    else:
                        #valid_data = data.flatten()
                        if 'sector' in list(self.ds.dims):
                            
                            total_sectors = len(self.ds.sector)
                            if i==0:
                                logging.info(f"Checking sectors: total sectors: {total_sectors}")
                            data = []
                            for i_sector in range(0, total_sectors-1):
                                #if self.ds.sector[i_sector].values != 'Agriculture' or self.ds.sector[i_sector] != 'CDR EW':
                                data_i = data_array.isel(time=i,sector=i_sector)
                                
                                if np.isnan(data_i).all():
                                    logging.info(
                                        f"All nans for sector='{self.ds.sector[i_sector].values}' at time={i}"
                                    )
                                else:
                                    if np.isnan(data_i).any():
                                        logging.info(
                                            f'Some nans for sector={self.ds.sector[i_sector].values} at time={i}'
                                        )
                                        data.append(data_i.values)
                            #data = data_array.isel(time=i).values
                        else:
                            data = data_array.isel(time=i)
                        
                        valid_data = np.array(data) 


                    result_timestep = 0
                    
                    
                    if np.isnan(valid_data.astype(np.float)).any():

                        result_timestep += 1
                        timesteps_err.append(i)
                        

                        # This is for saving NaN locations 
                        # Delete later if not needed
                        # ---- start

                        '''
                        lat_nans =  data_array.lat.values
                        lon_nans =  data_array.lon.values
                        
                        nan_locations = np.isnan(valid_data) 
                        nan_locations_da = xr.DataArray(nan_locations,dims=["lat","lon"],
                                                        coords=[('lat', lat_nans),('lon', lon_nans)])
                        nan_locations_da.name = 'nan_locations'
                        
                        nans_dir = f"nans_data/{self.file.name}"
                        if not os.path.exists(nans_dir):
                            os.makedirs(nans_dir)
                        
                        encoding = {'nan_locations': {'_FillValue': 1.}}       
                        nan_locations_da.to_netcdf(f"{nans_dir}/nan_locations_{i}.nc",encoding=encoding)
                        '''
                        
                        # ---- end
                            
                    self.results['spatial_completeness'].append(result_timestep)
                
                
                if timesteps_err != []:
                    if len(timesteps_err) == len(data_array.time.values):
                        logging.error(
                            f'Unexpected NaN(s) found in {var} at all timesteps {timesteps_err}'
                        ) 
                    else:
                        logging.error(
                            f'NaN(s) found in {var} at timesteps {timesteps_err}'
                        ) 

            else:
               
                logging.error(
                    f'error: File does not contain time variable'
                )
