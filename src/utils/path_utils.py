from pathlib import Path
import logging


def get_file_type(file_name) -> str:    
    """
    Return the type of the file extracted from the file name:
    - "multiple-management", "multiple-states", "multiple-transitions" for landuse
    - "em-AIR-anthro", "em-anthro", ... for emissions
    data_type (landuse or emissions) is defined based on this
    """

    filename_firstpart = file_name.split('_')[0]
    if 'multiple' in filename_firstpart:
        #print(f"debug: {filename_firstpart} -> landuse")
        file_type = filename_firstpart 
        varname = ''
    else:
        #print(f"debug: {filename_firstpart} -> emissions")
        s1 = filename_firstpart.split('-')[1:]
        file_type = '-'.join(s1)
        varname = filename_firstpart.replace('-','_')
    logging.info(f'Variable name will be checked for the file type {file_type}')
    return [varname, file_type, filename_firstpart]
  

def get_activity_id(file_name) -> str:
    """
    Get the activity id from the file name: 
    input4MIPs
    """
    activity_id = ""
    try:
        activity_id = file_name.split('_')[1] 
        logging.info(f'Recognized activity id {activity_id}')
    except:
        logging.warning(f'Not possible to recognize activity id in the file {file_name}')

    return activity_id

def get_dataset_category(file_name) -> str:
    """
    Get the dataset category from the file name:
    emissions or landState
    """
    dataset_category = ""
    try:
        dataset_category = file_name.split('_')[2] 
        logging.info(f'Recognized dataset category {dataset_category}')
    except:
        logging.warning(f'Not possible to recognize dataset category in the file {file_name}')

    return dataset_category


def get_target_mip(file_name) -> str:
    """
    Get the target mip from the file name:
    ScenarioMIP
    """
    target_mip = ""
    try:
        target_mip = file_name.split('_')[3] 
        logging.info(f'Recognized target mip {target_mip}')
    except:
        logging.warning(f'Not possible to recognize target mip in the file {file_name}')

    return target_mip


def get_source_id(file_name) -> str:
    """
    Get the source id from the file name:
    e.g. IAMC-AIM-ssp370-1-1
    """
    source_id = ""
    try:
        source_id = file_name.split('_')[4] 
        logging.info(f'Recognized source id {source_id}')
    except:
        logging.warning(f'Not possible to recognize source id in the file {file_name}')

    return source_id


def get_grid_type(file_name) -> str:
    """
    Get the grid type from the file name:
    gn or gr
    """
    grid_type = ""
    try:
        grid_type = file_name.split('_')[5] 
        if (grid_type == 'gn' or grid_type == 'gr'):
            logging.info(f'Recognized grid label {grid_type}')
        else:
            logging.warning(f"Grid label expected: 'gn' or 'gr', found: {grid_type}")
    except:
        logging.warning(f'Not possible to recognize grid label in the file {file_name}')

    return grid_type    


def get_dates_range(file_name) -> str:
    """
    Get the year range from the file name and check it. We suppose that the years should be in 1900-2500 range
    """

    try:
        dates_range = file_name.split('_')[6].split('.')[0]
        logging.info(f'Processing dates range {dates_range}')
        try: 
            start_date = dates_range.split('-')[0]
            logging.info(f'Recognized start date {start_date}')
            if (start_date.isnumeric()):
                start_year = int(start_date[0:4])
                if start_year<1900 or start_year>2500:
                    logging.error(f'Incorrect start year {start_date[0:4]} in the file {file_name} (should be in the range 1900-2500). ')                                
        except:
            return '0000'
        
        try:
            end_date = dates_range.split('-')[1]
            logging.info(f'Recognized end date {end_date}')
            if (end_date.isnumeric()):
                end_year = int(end_date[0:4])
                if end_year<1900 or end_year>2500:
                    logging.error(f'Incorrect end year {end_date[0:4]} in the file {file_name} (should be in the range 1900-2500). ')
                                             
        except:
            return '0000'
    except:
        logging.error(f'Not possible to recognize dates range in the file {file_name}')
        return '0000'

    return dates_range   



    
