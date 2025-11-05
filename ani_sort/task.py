from ani_sort.core import AniSort
from ani_sort.logging import setup_logger
from ani_sort.config_manager import load_config

def run_sort_task(input_folder, output_folder=None, dryrun=False, verbose=False):
    logger = setup_logger(verbose)
    config = load_config()
    sorter = AniSort(input_folder, output_folder, config, logger)
    sorter.process(dryrun=dryrun)
    return {
        "input": str(input_folder),
        "output": str(output_folder or config.general.default_output),
        "status": "success",
    }
