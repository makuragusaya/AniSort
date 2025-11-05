import os
from ani_sort.utils import sanitize_filename, get_all_files
from ani_sort.metadata import extract_groups, get_ani_info
from pathlib import Path
from typing import Union
import re
import logging
from datetime import datetime
import json
import uuid


SUFFIX_MAP = {
    "chs": ".zh-CN",
    "sc": ".zh-CN",
    "jpsc": ".zh-CN",
    "scjp": ".zh-CN",
    "cht": ".zh-TW",
    "tc": ".zh-TW",
    "jptc": ".zh-TW",
    "tcjp": ".zh-TW",
}


class AniSort(object):

    def __init__(
        self,
        path: Union[str, Path],
        parent_dir: Union[str, Path] = None,
        config=None,
        logger=None,
    ) -> None:

        self.path: Path = Path(path.strip("\"'")) if isinstance(path, str) else path
        self.config = config
        self.logger = logger or logging.getLogger(__name__)

        self.ani_info: dict = get_ani_info(self.path.stem, self.config, self.logger)
        self.season: int = self.ani_info["season"]
        self.ani_name: str = (
            f'{self.ani_info["name"]} ({self.ani_info["date"]})'.replace(
                ":", "："
            ).replace("?", "？")
        )
        self.extra_info: dict = extract_groups(self.path.stem)
        self.group_name: str = self.extra_info["group"]

        self.parent_dir: str = (
            f"{str(parent_dir).rstrip('/')}/{sanitize_filename(self.ani_name)}"
        )

        self.config.patterns: dict = [
            {**p, "regex": re.compile(p["regex"])} for p in self.config.patterns
        ]

        self.table: dict = {
            str(file): self.normalize(file) for file in get_all_files(self.path)
        }

        self.task_id = uuid.uuid4().hex[:8]
        self.start_time = datetime.now()
        self.logger.info(f"[TASK {self.task_id}] Started sorting: {self.path}")

        self.logger.debug("path: %s", self.path)
        self.logger.debug("path.stem: %s", self.path.stem)
        self.logger.debug("season: %s", self.season)
        self.logger.debug("ani_info: %s", self.ani_info)
        self.logger.debug("ani_name: %s", self.ani_name)
        self.logger.debug("extra_info: %s", self.extra_info)
        self.logger.debug("group_name: %s", self.group_name)
        self.logger.debug("parent_dir: %s", self.parent_dir)

    def parse(self, name: str) -> dict:
        """解析番剧文件名
        name: 番剧文件名
        """
        for p in self.config.patterns:
            if match := p["regex"].search(name):
                if p["type"] == "SE_EP":
                    season, match_2 = int(match[1]), match[2]
                else:
                    match_2: str = match[1] if p["type"] == "EP" else match[2] or "1"
                    season: int = self.season

                # 处理第0集的情况
                if (match2 := re.match(r"(\d+)(?:[v|_]\d+){0,1}", match_2)) and int(
                    match2[1]
                ) == 0:
                    return None

                return {
                    **p,
                    "season": f"{season:02d}",
                    "episode": (
                        f"{int(match_2):02d}"
                        if match_2.isdigit()
                        else match_2.split("v")[0]
                    ),
                    "raw_match": match.group(),
                    "match_1": match[1],
                }

        return None

    def normalize(self, path: Path) -> str:
        """获取文件规范化命名
        path: 文件路径
        """
        if (parse_info := self.parse(path.name)) and parse_info["normalize"]:
            if (suffix := path.suffix.lower()) == ".ass":
                suffix_sub: str = SUFFIX_MAP.get(path.stem.split(".")[-1].lower(), "")
                # TODO: Quick and dirty fix — refine later.
                if suffix_sub == ".zh-TW" and self.config.general.chinese_traditional:
                    suffix_sub = suffix_sub + ".forced"
                elif (
                    suffix_sub == ".zh-CN"
                    and not self.config.general.chinese_traditional
                ):
                    suffix_sub = suffix_sub + ".forced"
                suffix: str = suffix_sub + suffix
            if suffix in self.config.ignore_exts:
                return "ignore"

            return (
                f"{self.parent_dir}/"
                + parse_info["normalize"].format(
                    ani_name=self.ani_name,
                    raw_match=(
                        parse_info["raw_match"].strip(" []")
                        if parse_info["type"] == "Label"
                        else parse_info["raw_match"]
                    ),
                    season=parse_info["season"],
                    episode=parse_info["episode"],
                    group=self.group_name,
                )
                + suffix
            )

        suffix = path.suffix.lower()
        if suffix in self.config.ignore_exts:
            return "ignore"

        return f"{self.parent_dir}/Unknown_Files/{path.name}"

    def move_original_folder(self, dryrun=False) -> None:
        target_root = Path(self.config.general.original_archive_dir)
        target_root.mkdir(exist_ok=True, parents=True)
        dest_dir = target_root / self.path.name
        if dryrun:
            self.logger.debug(
                f"[DRYRUN] Would move original folder:\n  {self.path} => {dest_dir}"
            )
        else:
            try:
                self.logger.info(
                    f"[MOVE] Moving original folder:\n  {self.path} => {dest_dir}"
                )
                self.path.rename(dest_dir)
            except Exception as e:
                self.logger.exception(f"[WARN] Failed to move original folder: {e}")

    def _write_task_log(self, status="success", duration=0):
        entry = {
            "task_id": getattr(self, "task_id", "unknown"),
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "input": str(self.path),
            "output": str(self.parent_dir),
            "group": getattr(self, "group_name", None),
            "anime": getattr(self, "ani_name", None),
            "season": getattr(self, "season", None),
            "status": status,
            "duration": duration,
        }

        history_file = Path("tasks/history.json")
        history_file.parent.mkdir(exist_ok=True)
        data = []

        try:
            if history_file.exists():
                data = json.loads(history_file.read_text(encoding="utf-8"))
        except Exception as e:
            self.logger.warning(f"Failed to read task history: {e}")

        data.append(entry)

        try:
            history_file.write_text(json.dumps(data, indent=2, ensure_ascii=False))
            self.logger.debug(f"[TASK {self.task_id}] Logged task result to {history_file}")
        except Exception as e:
            self.logger.error(f"Failed to write task log: {e}")

    def _handle_link(self, src_path, dest_path, ext):
        try:
            os.link(src_path, dest_path)
            self.logger.info(
                f"Arrange: [{ext}] {src_path.name} (Linked)\n => {dest_path}"
            )
        except Exception as e:
            self.logger.exception(
                f"WARN: Cannot create hard link for {src_path.name} Error: {e}"
            )
            self.logger.error(f"[TASK {self.task_id}] Failed: {e}")
            self._write_task_log(status="failed")

    def process(self, dryrun=False, move=False) -> None:
        # return
        dest_dirs: dict = {Path(dest).parent for dest in self.table.values()}
        for d in dest_dirs:
            if dryrun:
                self.logger.debug(f"[DRYRUN] Would create directory: {d}")
            else:
                d.mkdir(parents=True, exist_ok=True)

        for src, dest in self.table.items():
            src_path = Path(src)
            dest_path = Path(dest)
            ext = src_path.suffix.upper()

            if dest == "ignore":
                self.logger.debug(f"Ignore [{ext}] : {src_path}\n ")
            elif not dest_path.exists():
                if dryrun:
                    self.logger.debug(
                        f"[DRYRUN] [{ext}] Would link: {src_path}\n => {dest_path}"
                    )
                else:
                    self._handle_link(src_path, dest_path, ext)
            else:
                self.table[src] = src_path.name
                self.logger.info(f"Skipped: Target file {dest_path} alreday exists.")

        if self.config.general.ignore_file:
            for root in Path(self.parent_dir).rglob("*/"):
                if root.name in ["Interviews", "Other", "Unknown_Files"]:
                    if dryrun:
                        self.logger.debug(f"[DRYRUN] Would write .ignore in: {root}")
                    else:
                        (root / ".ignore").write_text("", encoding="utf-8")

        if self.config.general.comparison_table:
            if dryrun:
                self.logger.debug(
                    f"[DRYRUN] Would append Comparison_Table.txt in {self.parent_dir}"
                )
            else:
                with open(
                    f"{self.parent_dir}/Comparison_Table.txt", "a", encoding="utf-8"
                ) as file:
                    file.write(
                        "\n"
                        + "\n\n".join(
                            "{}\n└── {}".format(
                                "/".join(Path(v).parts[-2:]), Path(k).name
                            )
                            for k, v in self.table.items()
                        )
                    )

        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        self.logger.info(f"[TASK {self.task_id}] Finished in {duration:.2f}s")

        self._write_task_log(status="success", duration=duration)
