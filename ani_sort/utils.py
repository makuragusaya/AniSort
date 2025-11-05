from typing import List
from pathlib import Path
import difflib


def sanitize_filename(name: str) -> str:
    """格式化文件名
    name: 文件名
    """
    return (
        name.replace("\\", "_")
        .replace("/", "_")
        .replace("|", "_")
        .replace("?", "？")
        .replace(":", "：")
        .replace("*", "_")
        .replace('"', "_")
        .replace("<", "《")
        .replace(">", "》")
        .replace(".", "_")
    )


def get_all_files(path: Path) -> List[Path]:
    """获取文件夹内所有文件，先按层级分类，再按相似度排序"""
    if path.is_file():
        return [path]

    files_by_level = {}
    for f in path.rglob("*"):
        if f.is_file():
            files_by_level.setdefault(len(f.relative_to(path).parts), []).append(f)

    return [
        file
        for level in sorted(files_by_level.keys())
        for file in sorted(
            files_by_level[level],
            key=lambda x: difflib.SequenceMatcher(None, str(x), str(path)).ratio(),
            reverse=True,
        )
    ]
