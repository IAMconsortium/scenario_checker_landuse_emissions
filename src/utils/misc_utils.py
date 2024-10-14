import json
from typing import Dict
from pathlib import Path
import logging

import numpy as np


def read_config_file(config_file_path: str) -> Dict:
    
    with open(config_file_path, 'r') as f:
        config = json.load(f)

    return config


def check_config_file(config: Dict) -> Dict:
    """
    Check that all needed keys are present in the config dictionary
    """
    # Check directory exists
    assert 'check_directory' in config
    assert Path(config['check_directory']).exists()

    # Check flags. If not present, default to true
    flags = ['flag_spatial_completeness', 'flag_spatial_consistency',
             'flag_temporal_completeness', 'flag_temporal_consistency',
             'flag_valid_ranges', 'flag_states_transitions'
            ]

    for flag in flags:
        if flag in config:
            assert isinstance(config[flag], bool)
        else:
            config[flag] = True

    else:
        assert Path(config['mask_landuse']).exists()

    # Check log path. If not present, default to "logs"
    if 'log_path' not in config:
        config['log_path'] = 'logs'

    return config



def get_file_re_pattern(data_source: str) -> str:
    """
    Get the regex pattern that should follow every file:
    variable name + activity_id + dataset_category + target_mip + source_id + grid + YYYYMM/YYYY (start date) + YYYYMM/YYYY (end date)
    """

    logging.info(
        f'Found {data_source} variable(s)'
    )
    
    if data_source == 'landuse':
        return r'multiple-[a-zA-Z0-9-_]{1,200}_input4MIPs_landState_[a-zA-Z0-9-._]{1,200}_gn_(\d{4})\-(\d{4})\.nc$'
    else:
        return r'[a-zA-Z0-9-_]{1,400}_input4MIPs_emissions_[a-zA-Z0-9-._]{1,400}_gn_(\d{6})\-(\d{6})\.nc$'

    
    

def get_valid_data(data: np.ndarray, mask: np.ndarray) -> np.array:
    """
    Use the mask file to return the data values that should be valid (with no NaNs)
    """
   
    land_values = np.ma.masked_array(data, mask)
    return land_values

