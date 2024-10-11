import sys
import logging
from pathlib import Path
import datetime

def update_log_paths(root_dir, check_dir: Path):
    """
    Update the log message paths
    """
    # Remove all old handlers
    log = logging.getLogger()  # root logger
    for handler in log.handlers[:]:  # remove all old handlers
        log.removeHandler(handler)

    log = logging.getLogger()
    log_format = logging.Formatter('%(levelname)s: %(message)s')

    # Create directory for logs (a new one for each run) 
    time_now = datetime.datetime.now() 
    timestamp = f'{time_now.year}-{time_now.month}-{time_now.day}-{time_now.hour}-{time_now.minute}'
    log_dir_name = f'{root_dir}/{check_dir.name}___{timestamp}'
    log_dir = Path(log_dir_name)
    counter = 1
    while log_dir.exists():
        log_dir = Path(f'{log_dir_name}___{counter}')
        counter += 1
    
    log_dir.mkdir(parents=True) #, exist_ok=False)
        
    # Set up logging to terminal
    handler_stdout = logging.StreamHandler(stream=sys.stdout)
    handler_stdout.setLevel('INFO')
    handler_stdout.setFormatter(log_format)
    log.addHandler(handler_stdout)

    # Set up logging all info to general log file
    handler_general = logging.FileHandler(
        filename=f'{log_dir}/{check_dir.name}_output.log',
        mode='w+'
        )
    handler_general.setLevel('DEBUG')
    handler_general.setFormatter(log_format)
    log.addHandler(handler_general)

    # Set up logging only errors to error file
    handler_errors = logging.FileHandler(
        filename=f'{log_dir}/{check_dir.name}_errors.log',
        mode='w+'
        )
    handler_errors.setLevel('ERROR')
    handler_errors.setFormatter(log_format)
    log.addHandler(handler_errors)
