import requests


def call_tmdb(
    api_key: str,
    url: str,
    params: dict | None = None,
    proxies: dict | None = None,
    logger=None,
) -> dict:
    params = params or {}
    proxies = proxies or {}
    if logger:
        logger.debug(f"TMDB request to {url} with {params}")

    try:
        res = requests.get(
            url=url,
            params={**params, "language": "zh-CN", "api_key": api_key},
            proxies=proxies,
            headers={"accept": "application/json"},
            timeout=60,
        )
        res.raise_for_status()
        return res
    except Exception as e:
        raise Exception(f"连接 TMDB 时发生错误：{e}")


def call_ai(api_key: str, content: str) -> str:
    try:
        res = requests.post(
            url="https://api.deepseek.com/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "deepseek-reasoner",
                "messages": [{"role": "user", "content": content}],
            },
        )
        res.raise_for_status()
        return res.json()["choices"][0]["message"]["content"]
    except Exception as e:
        raise Exception(f"连接 DeepSeek 时发生错误：{e}")
