import argparse
from ani_sort.task import run_sort_task


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

    status = run_sort_task(args.input, args.output, args.dryrun, args.verbose)["status"]
    print(f"Run sort task: {status}")


if __name__ == "__main__":
    main()
