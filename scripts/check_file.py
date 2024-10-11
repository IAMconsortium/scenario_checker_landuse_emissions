import argparse
from pathlib import Path
import logging


from checkers.directory_checker import DirectoryChecker


def parse_arguments():
    parser = argparse.ArgumentParser(description='File check argument parser')
    parser.add_argument('file', type=str,
                        help='File to which apply the checks')
    parser.add_argument('--spatial-completeness', type=bool, default=True,
                        help='Whether to apply spatial completeness check')
    parser.add_argument('--spatial-consistency', type=bool, default=True,
                        help='Whether to apply spatial consistency check')
    parser.add_argument('--temporal-consistency', type=bool, default=True,
                        help='Whether to apply temporal consistency check')
    parser.add_argument('--valid-ranges', type=bool, default=True,
                        help='Whether to apply valid_ranges check')

    return parser.parse_args()


def create_symlink(file, temp_dir):

    if not file.exists():
        raise FileNotFoundError(
            f'File {file} does not exist'
        )

    # Create directory for symlink
    temp_dir.mkdir(exist_ok=False, parents=True)

    # Create symlink to file
    symlink_path = temp_dir / file.name
    symlink_path.symlink_to(file)


def delete_temp_dir(pth: Path):
    for item in pth.iterdir():
        if item.is_dir():
            delete_temp_dir(item)
        else:
            item.unlink()
    pth.rmdir()


def run_checker(args, temp_dir):

    config = {
        "check_directory": temp_dir,
        "references": args.references, 
        "metadata_file": "variable-metadata.json",
        "flag_file_name": True,
        "flag_standard_compliance": True,
        "flag_spatial_completeness": args.flag_spatial_completeness,
        "flag_spatial_consistency": args.flag_spatial_consistency,
        "flag_temporal_consistency": args.flag_temporal_consistency,
        "flag_valid_ranges": args.flag_valid_ranges,
        "flag_states_transitions": args.flag_states_transitions,
        "required_file_types": args.required_file_types,
        "required_variables": args.required_variables,
        "required_coords": args.required_coords,
        "required_attributes": args.required_attributes,
        "required_attributes_in_vars": args.required_attributes_in_vars,
        "logging_level": "WARNING"
    }

    logging.basicConfig(level=config['logging_level'])

    dschecker = DirectoryChecker(config)
    dschecker.run_checker()


def main():

    # Read args from command line
    args = parse_arguments()
    file = Path(args.file)

    # Define root path for temporary files
    temp_root = Path(
        args.base_path + '/tmp' 
        )
    
    # Replicate file tree inside temp dir
    temp_dir = temp_root / str(file.parents[0].absolute())[1:]

    # Create symlink inside temp dir
    create_symlink(file, temp_dir)

    # Run checker
    try:
        run_checker(args, temp_dir)
    except Exception:
        logging.error('An exception occurred during data check.')
        logging.error('Removing all temporary files')
        delete_temp_dir(temp_root)
        raise

    # Delete temporary files
    delete_temp_dir(temp_root)


if __name__ == '__main__':
    main()
