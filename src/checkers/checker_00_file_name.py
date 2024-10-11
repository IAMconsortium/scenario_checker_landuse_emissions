import logging
import re

from utils.misc_utils import get_file_re_pattern 

class FileNameChecker:
    """
    Check the file name
    """

    def __init__(self, dschecker):
        self.dschecker = dschecker
        self.required_file_types = dschecker.required_file_types

        # Read only attributes
        self.file_type = dschecker.file_type
        self.file = dschecker.file

        # Check status
        self.results = {}

    def run_checker(self):
        '''
        Run file name check
        '''
        
        # Ignore if it is a directory
        if not self.file.is_file():
            self.dschecker.is_valid = False
            self.results['file_name'] = 1
            logging.error(
                f'Found directory: {self.file.name}. Skipping all tests on this directory'
            )

        else:
            file_type_counter = 0
            for filetype in self.required_file_types:

                '''
                filetype can be: 
                emissions: "em-AIR-anthro", "em-AIR-anthro", "em-anthro", "em-openburning", "em-openburning-shares",
                # "em-SOLID-BIOFUEL-anthro", "em-SHP-anthro", "em-removal", "multiple-management", ...
                landuse: "multiple-management", "multiple-states", "multiple-transitions"
                '''
                if filetype in self.file_type:
                    file_type_counter += 1
            if (not file_type_counter):
                self.dschecker.is_valid = False
                self.results['file_name'] = 2
                logging.error(
                    f'File type {self.file_type} is not recognized in the file {self.file.name}. Skipping all tests on this file'
                )
                
            else: 
                if 'multiple' in self.file_type:
                    self.data_source = 'landuse' 
                else:
                    self.data_source = 'emissions'
    
                re_pattern = get_file_re_pattern(self.data_source)
                pattern = re.compile(re_pattern)
                if not pattern.match(self.file.name): 
                    self.dschecker.is_valid = False
                    self.results['file_name'] = 2
                    logging.error(
                        f'Found unexpected file: {self.file.name}. Skipping all tests on this file'
                    )

                else:
                    self.dschecker.is_valid = True
                    self.results['file_name'] = 0
