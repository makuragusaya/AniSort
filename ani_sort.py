import os
from utils import sanitize_filename
from config.config_manager import load_config
from pathlib import Path
from typing import Union
import difflib
import requests
import re
import sys

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
        self, path: Union[str, Path], parent_dir: Union[str, Path] = None
    ) -> None:
        self.path: Path = Path(path.strip("\"'")) if isinstance(path, str) else path

        self.season: int = None
        self.ani_info: dict = self.get_ani_info(self.path.stem)
        self.ani_name: str = (
            f'{self.ani_info["name"]} ({self.ani_info["date"]})'.replace(
                ":", "："
            ).replace("?", "？")
        )
        self.extra_info: dict = self.get_extra_info(self.path.stem)
        self.group_name: str = self.extra_info["group"]

        self.parent_dir: str = (
            f"{str(parent_dir).rstrip('/') if parent_dir else str(general.default_output).rstrip('/')}/{sanitize_filename(self.ani_name)}"
        )

        self.patterns: dict = [{**p, "regex": re.compile(p["regex"])} for p in patterns]

        self.table: dict = {
            str(file): self.normalize(file) for file in self.get_all_files(self.path)
        }

        print("path: ", self.path)
        print("path.stem: ", self.path.stem)
        print("season: ", self.season)
        print("ani_info: ", self.ani_info)
        print("ani_name: ", self.ani_name)
        print("extra_info: ", self.extra_info)
        print("group_name: ", self.group_name)
        print("parent_dir: ", self.parent_dir)

    def get_all_files(self, path: Path) -> list:
        """获取文件夹内所有文件，先按层级分类，再按相似度排序
        path: 文件路径
        """
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

    def call_ai(self, content: str):
        """调用 AI 进行番剧信息解析
        name: 番剧文件名
        """
        try:
            res = requests.post(
                url="https://api.deepseek.com/chat/completions",
                headers={
                    "Authorization": f"Bearer {ai.api}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "deepseek-reasoner",
                    "messages": [{"role": "user", "content": content}],
                },
                timeout=None,
            )
            res.raise_for_status()
            return res.json()["choices"][0]["message"]["content"]
        except Exception as e:
            raise Exception(f"连接 DeepSeek 时发生错误：{e}")

    def call_tmdb(self, url: str, params: dict = {}):
        try:
            res = requests.get(
                url=url,
                params={**params, "language": "zh-CN", "api_key": tmdb.api},
                proxies=general.proxies,
                headers={"accept": "application/json"},
                timeout=60,
            )
            res.raise_for_status()
            return res
        except Exception as e:
            raise Exception(f"连接 TMDB 时发生错误：{e}")

    def get_extra_info(self, stem: str) -> dict:
        candidates = re.findall(r"(?:\[|\()(.*?)(?:\]|\))", stem)

        # 定义要排除的模式：分辨率、年份、常见码率/色深标签
        ignore_patterns = [
            r"\d{3,4}p",  # 1080p / 2160p
            r"\d{4}",  # 年份 2023
            r"\b10bit\b",  # 10bit
            r"Ma10p",  # 常见 VCB/NC-Raws 编码标签
            r"HEVC|AVC|x265|x264",
        ]

        group = None
        others = []
        print("candidates:", candidates)

        for i, item in enumerate(candidates):
            if i == 0:
                group = item
                continue

            if any(re.search(pat, item, re.I) for pat in ignore_patterns):
                others.append(item)
                continue

            others.append(item)

        return {"group": group, "others": others}

    def get_ani_info(self, name: str) -> dict:
        """获取番剧的信息
        name: 番剧文件名
        """
        query: str = (
            print("调用 AI - 1") or self.call_ai(f"{name}\n\n{ai.prompt1}")
            if ai.call
            else (
                match := re.match(
                    r"(?i)(.+?)(?:[_\s-]*(?:s|season)\s*(\d+))?$",
                    re.sub(r"\s*(\[|\().*?(\]|\))\s*", "", name),
                )
            )[1]
        )
        res = print("调用 TMDB") or self.call_tmdb(
            url="https://api.themoviedb.org/3/search/tv", params={"query": query}
        )
        try:
            info: dict = res.json()["results"][0]
            if tmdb.manual and res.json()["results"]:
                print(
                    "\n"
                    + "\n".join(
                        f'{i}、{j["name"]} ({j["first_air_date"] if j["first_air_date"] else "None"})'
                        for i, j in enumerate(res.json()["results"])
                    )
                    + "\n"
                )

                if (_input := input("请输入你想选择的结果的序号：")).isdigit():
                    info: dict = res.json()["results"][int(_input)]
        except Exception as e:
            raise Exception(f"无法搜索到该动漫，请更改文件夹名称后再试一次 {e}")

        if ai.call:
            seasons_info: list = self.call_tmdb(
                url=f'https://api.themoviedb.org/3/tv/{info["id"]}'
            ).json()["seasons"]
            seasons_conten: list = "\n".join(
                [
                    f'{j["name"]}: {i + 1}'
                    for i, j in enumerate(
                        seasons_info[1:]
                        if seasons_info[0]["name"] == "特别篇"
                        else seasons_info
                    )
                ]
            )
            self.season: int = print("调用 AI - 2") or int(
                self.call_ai(f"{name}\n\n{seasons_conten}\n\n{ai.prompt2}")
            )
        else:
            self.season: int = int(match[2]) if match[2] else 1

        return {
            "name": info["name"],
            "date": info["first_air_date"].split("-")[0] or "年份未知",
        }

    def parse(self, name: str) -> dict:
        """解析番剧文件名
        name: 番剧文件名
        """
        for p in self.patterns:
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
                if suffix_sub == ".zh-TW" and general.trad_chinese:
                    suffix_sub = suffix_sub + ".forced"
                elif suffix_sub == ".zh-CN" and not general.trad_chinese:
                    suffix_sub = suffix_sub + ".forced"
                suffix: str = suffix_sub + suffix
            if suffix in config.ignore_exts:
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
        if suffix in config.ignore_exts:
            return "ignore"

        return f"{self.parent_dir}/Unknown_Files/{path.name}"

    def _handle_link(self, src_path, dest_path, ext):
        try:
            os.link(src_path, dest_path)
            print(f"Arrange: [{ext}] {src_path.name} (Linked)\n => {dest_path}")
        except Exception as e:
            print(f"WARN: Cannot create hard link for {src_path.name} Error: {e}")

    def main(self, dryrun=False, verbose=False) -> None:
        # return
        dest_dirs: dict = {Path(dest).parent for dest in self.table.values()}
        for d in dest_dirs:
            if dryrun:
                print(f"[DRYRUN] Would create directory: {d}")
            else:
                d.mkdir(parents=True, exist_ok=True)

        for src, dest in self.table.items():
            src_path = Path(src)
            dest_path = Path(dest)
            ext = src_path.suffix.upper()

            if dest == "ignore":
                if verbose:
                    print(f"Ignore [{ext}] : {src_path}\n ")
            elif not dest_path.exists():
                if dryrun:
                    print(f"[DRYRUN] [{ext}] Would link: {src_path}\n => {dest_path}")
                else:
                    self._handle_link(src_path, dest_path, ext)
            else:
                self.table[src] = src_path.name
                print(f"Skipped: Target file {dest_path} alreday exists.")

        if general.generate_ignore_file:
            for root in Path(self.parent_dir).rglob("*/"):
                if root.name in ["Interviews", "Other", "Unknown_Files"]:
                    if dryrun:
                        print(f"[DRYRUN] Would write .ignore in: {root}")
                    else:
                        (root / ".ignore").write_text("", encoding="utf-8")

        if general.generate_comparison_table:
            if dryrun:
                print(
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


if __name__ == "__main__":
    try:
        config = load_config()
    except Exception as e:
        print(f"[FATAL] Failed to load configuration: {e}")
        sys.exit(1)

    general = config.general
    tmdb = config.tmdb
    ai = config.ai
    patterns = config.patterns

    output_dir = None
    if len(sys.argv) > 1:
        input_folder = sys.argv[1]
        print("input folder: ", input_folder)
    if len(sys.argv) > 2:
        output_dir = sys.argv[2]
        print("output dir: ", output_dir)

    AniSort(input_folder, output_dir).main(dryrun=True)
