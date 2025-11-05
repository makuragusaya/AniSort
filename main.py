import argparse
import sys
from ani_sort.config_manager import load_config
from ani_sort.logging import setup_logger
from ani_sort.core import AniSort


def main():
    parser = argparse.ArgumentParser(description="Anime BD Organizer (AniSort) CLI")
    parser.add_argument("input", help="Input folder path")
    parser.add_argument("output", nargs="?", help="Optional output folder path")
    parser.add_argument(
        "--dryrun", action="store_true", help="Preview only, no changes"
    )
    parser.add_argument("--verbose", action="store_true", help="Show detailed logs")
    parser.add_argument(
        "--move",
        action="store_true",
        help="Move the original input folder to a designated location after sorting",
    )
    args = parser.parse_args()

    logger = setup_logger(verbose=args.verbose)

    try:
        config = load_config()
    except Exception as e:
        logger.critical(f"Failed to load configuration: {e}")
        sys.exit(1)

    sorter = AniSort(args.input, args.output, config, logger)
    sorter.main(dryrun=args.dryrun)

    if args.move and config.features.get("move_original", False):
        sorter.move_original_folder(dryrun=args.dryrun)


if __name__ == "__main__":
    main()
