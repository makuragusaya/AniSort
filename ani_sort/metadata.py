import re
from ani_sort.api import call_tmdb, call_ai


def extract_groups(stem: str) -> dict:
    """提取字幕组与其他标签信息"""
    candidates = re.findall(r"(?:\[|\()(.*?)(?:\]|\))", stem)
    ignore_patterns = [
        r"\d{3,4}p",
        r"\d{4}",
        r"\b10bit\b",
        r"Ma10p",
        r"HEVC|AVC|x265|x264",
    ]

    group = candidates[0] if candidates else None
    others = [
        c
        for c in candidates[1:]
        if not any(re.search(p, c, re.I) for p in ignore_patterns)
    ]
    return {"group": group, "others": others}


def get_ani_info(name: str, config=None, logger=None) -> dict:
    """获取番剧的信息
    name: 番剧文件名
    """
    query: str = (
        logger.info("调用 AI - 1") or call_ai(config.ai.api, f"{name}\n\n{config.ai.prompt1}")
        if config.ai.call
        else (
            match := re.match(
                r"(?i)(.+?)(?:[_\s-]*(?:s|season)\s*(\d+))?$",
                re.sub(r"\s*(\[|\().*?(\]|\))\s*", "", name),
            )
        )[1]
    )
    res = logger.info("调用 TMDB") or call_tmdb(
        config.tmdb.api,
        url="https://api.themoviedb.org/3/search/tv",
        params={"query": query},
        proxies=config.general.proxies,
        logger=logger,
    )
    try:
        info: dict = res.json()["results"][0]
        if config.tmdb.manual and res.json()["results"]:
            logger.info(
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

    if config.ai.call:
        seasons_info: list = call_tmdb(
            config.tmdb.api,
            url=f'https://api.themoviedb.org/3/tv/{info["id"]}',
            proxies=config.general.proxies,
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
        season: int = logger.info("调用 AI - 2") or int(
            call_ai(config.ai.api, f"{name}\n\n{seasons_conten}\n\n{config.ai.prompt2}")
        )
    else:
        season: int = int(match[2]) if match[2] else 1

    return {
        "name": info["name"],
        "date": info["first_air_date"].split("-")[0] or "年份未知",
        "season": season,
    }
