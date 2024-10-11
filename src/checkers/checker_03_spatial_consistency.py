import logging
#import csv
import numpy as np


class SpatialConsistencyChecker:
    """
    Check that the lon/lat grid points correspond to the reference file
    """

    def __init__(self, dschecker):
        self.dschecker = dschecker

        self.file = dschecker.file
        self.ds = dschecker.ds
        self.expected_lat = dschecker.expected_lat
        self.expected_lon = dschecker.expected_lon

        # Check results
        self.results = {}

    def validate_grid(self, lon: np.array, lat: np.array) -> bool:
       
        grid_equal_lon = -1
        grid_equal_lat = -1

        if (not np.array_equal(lon,self.expected_lon)) and (not np.array_equal(lon[::-1],self.expected_lon)):
            
            logging.error(
                f"Grid for lon does not correspond to the expected one:"
                f"lon: {lon}, expected lon: {self.expected_lon}"
            )
            grid_equal_lon = 0

        else:
            grid_equal_lon = 1

        if (not np.array_equal(lat,self.expected_lat)) and (not np.array_equal(lat[::-1],self.expected_lat)):
            logging.error(
                f"Grid for lat does not correspond to the expected one:"
                f"lat: {lat}, expected lat: {self.expected_lat}"
            )
            
            grid_equal_lat = 0
            
        else:
            grid_equal_lat = 1
        

        if (grid_equal_lon == 0) or (grid_equal_lat == 0):
            return False
        else:
            return True

        
    def run_checker(self):
        """
        Run spatial consistency check
        """
        try:
            lat = getattr(self.ds, 'lat').values
            logging.info(
                f"Found the latitude dimension with the name 'lat' "
            )
        except AttributeError:
            try: 
                lat = getattr(self.ds, 'latitude').values
                logging.info(
                    f"Found the latitude dimension with the name 'latitude' "
                )
            except AttributeError:
                self.results['spatial_consistency'] = -1
                logging.error(
                    f'Missing compulsory attribute {["lat"]} or {["latitude"]}. Skipping spatial consistency check...'
                )
            #return 1

        try:            
            lon = getattr(self.ds, 'lon').values
            logging.info(
                f"Found the longitude dimension with the name 'lon' "
            )
        except AttributeError:
            try: 
                lon = getattr(self.ds, 'longitude').values
                logging.info(
                    f"Found the longitude dimension with the name 'longitude' "
                )
            except AttributeError:
                self.results['spatial_consistency'] = -1
                logging.error(
                    f'Missing compulsory attribute {["lon"]} or {["longitude"]}. Skipping spatial consistency check...'
                )
            
        
        if ('spatial_consistency' in self.results.keys()):
            return 1
        else:
            self.results['spatial_consistency'] = 0
            if not self.validate_grid(lon, lat):
                self.results['spatial_consistency'] = 3
        


       


