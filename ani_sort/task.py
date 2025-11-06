from datetime import datetime
from ani_sort.core import AniSort
from ani_sort.logging import setup_logger
from ani_sort.config_manager import load_config
from ani_sort.db import SessionLocal, Task, get_or_create_anime, WatchedFolder


def run_sort_task(
    input_path,
    output_dir=None,
    *,
    dryrun: bool | None = None,
    verbose: bool | None = None,
    move: bool | None = None,
    subset: bool | None = None,
    is_cli: bool = False,
):

    config = load_config()
    effective_dryrun = dryrun if is_cli and dryrun is not None else False
    effective_move = (
        move
        if is_cli and move is not None
        else config.features.get("move_original", False)
    )
    effective_subset = (
        subset
        if is_cli and subset is not None
        else config.features.get("subset_ass", False)
    )
    effective_verbose = (
        subset
        if is_cli and subset is not None
        else config.features.get("verbose", False)
    )

    logger = setup_logger(effective_verbose)

    logger.info(
        f"Running task with options: dryrun={effective_dryrun}, move={effective_move}, subset={effective_subset}"
    )

    session = SessionLocal()

    task = Task(
        input_path=str(input_path), output_path=str(output_dir), status="running"
    )
    session.add(task)
    session.commit()

    watched = session.query(WatchedFolder).filter_by(path=input_path).first()
    if watched:
        watched.status = "processing"
        watched.task_id = task.id
        session.commit()

    try:
        sorter = AniSort(input_path, output_dir, config, logger)
        sorter.process(dryrun=effective_dryrun)
        task.status = "success"
        task.success = True
    except Exception as e:
        session.rollback
        task.status = "failed"
        task.success = False
        task.error_msg = str(e)
        session.merge(task)
    finally:
        task.ended_at = datetime.now()
        task.output_path = sorter.parent_dir
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
            if watched:
                watched.status = "processed"
        elif anime.status == "done":
            anime.status = "update failed"
        else:
            anime.status = "failed"

        task.anime_id = anime.id

        if session.is_active:
            logger.info("Session is active, committing changes")
        else:
            logger.warning("Session inactive, performing rollback before commit")
            session.rollback()

        try:
            session.commit()
        except Exception as e:
            logger.error(f"Commit failed: {e}")
            session.rollback()

    # MoveOriginal
    if effective_move:
        sorter.move_original_folder(dryrun=effective_dryrun)

    # Subset
    if effective_subset:
        sorter.subset_ass(dryrun=effective_dryrun)

    return {
        "input": str(sorter.path),
        "output": str(sorter.parent_dir),
        "status": "success",
    }
