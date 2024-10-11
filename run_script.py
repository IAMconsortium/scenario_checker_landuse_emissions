import logging
import time
import argparse

from checkers.directory_checker import DirectoryChecker
from utils.misc_utils import read_config_file


def parse_arguments():
    """
    Parse config file path form terminal
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('config', help='Path to the config json file', type=str)
    return parser.parse_args()


def main():
    """
    Run checker on a given directory.
    All configuration parameters must be specified in a config json file.
    """
    # Parse arguments
    args = parse_arguments()

    # Read configuration file
    config = read_config_file(args.config)

    # Initialize and run checker
    t_start = time.perf_counter()
    checker = DirectoryChecker(**config)
    checker.run_checker()
    t_end = time.perf_counter()

    # Report elapsed time
    print(f"Elapsed time: {t_end - t_start:.3f} seconds(s)")


if __name__ == '__main__':
    main()
