from datetime import datetime
from ani_sort.core import AniSort
from ani_sort.logging import setup_logger
from ani_sort.config_manager import load_config
from ani_sort.db import SessionLocal, Task, get_or_create_anime


def run_sort_task(input_path, output_dir=None, dryrun=False, verbose=False, move=False):
    logger = setup_logger(verbose)
    config = load_config()

    session = SessionLocal()

    task = Task(
        input_path=str(input_path), output_path=str(output_dir), status="running"
    )
    session.add(task)
    session.commit()

    try:
        sorter = AniSort(input_path, output_dir, config, logger)
        sorter.process(dryrun=dryrun)
        task.status = "success"
        task.success = True
    except Exception as e:
        task.status = "failed"
        task.success = False
        task.error_msg = str(e)
    finally:
        task.ended_at = datetime.now()
        anime = get_or_create_anime(
            session,
            sorter.ani_name,
            sorter.group_name,
            sorter.season,
            sorter.parent_dir,
            sorter.tmdb_id,
            sorter.poster_path,
        )

        if task.success:
            anime.status = "done"
            anime.last_updated = datetime.now()
        elif anime.status == "done":
            anime.status = "update failed"
        else:
            anime.status = "failed"

        task.anime_id = anime.id
        session.commit()

    # MoveOriginal
    if move and config.features.get("move_original", False):
        sorter.move_original_folder(dryrun=dryrun)

    # Subset
    if config.features.get("subset_ass", False):
        sorter.subset_ass(dryrun=dryrun)

    return {
        "input": str(sorter.path),
        "output": str(sorter.parent_dir),
        "status": "success",
    }
