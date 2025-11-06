from ani_sort.core import AniSort
from ani_sort.logging import setup_logger
from ani_sort.config_manager import load_config
from ani_sort.db import SessionLocal, Anime, Task


def run_sort_task(
    input_path, output_dir=None, dryrun=False, verbose=False, move=False
):
    logger = setup_logger(verbose)
    config = load_config()

    session = SessionLocal()

    task = Task(input_path=str(input_path), status="running")
    session.add(task)
    session.commit()

    try:
        sorter = AniSort(input_path, output_dir, config, logger)
        sorter.process(dryrun=dryrun)
        task.status = "success"
        task.success = True
    except Exception as e:
        task.status = "failed"
        task.error_msg = str(e)
    finally:
        anime = Anime(
            name=sorter.ani_name,
            group_name=sorter.group_name,
            season=sorter.season,
            output_path=str(sorter.parent_dir),
        )
        session.add(anime)
        session.flush()  # 获取 anime.id
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
