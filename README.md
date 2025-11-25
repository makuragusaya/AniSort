## AniSort (Enhanced Edition)

A modernized, modular anime library organizer.
Automatically renames, restructures, and catalogs Blu-ray rips following Jellyfin/Plex conventions, with database integration and Web UI.

> Forked and extended from [bysansheng/AniSort](https://github.com/bysansheng/AniSort),
> with organization logic inspired by [mikusa 的媒体库管理方案](https://www.himiku.com/archives/how-i-organize-my-animation-library.html)

This project began as a fork of the original **AniSort** by @bysansheng, but has since been heavily refactored and expanded.  
While the core matching logic and naming patterns are inherited, the architecture, configuration system, and automation pipeline have been completely rewritten.

## Why this project 

The goal is to make the anime library organization fully automated and easier controllable. 
From folder monitoring to renaming, hardlinking, subtitle subsetting, and metadata integration.
So that your NAS or Jellyfin server always stays perfectly structured with minimal manual work.

## Improvements

- Database Integration
- Web UI 
- **New config system** with `.env` + yaml + Pydantic validation
- Introduce Hard link instead of move
- Logging system
- Subtitle Subset Integration
- Automatic Folder Watching

## Improvements & Roadmap

### Completed
- [x] Fully restructured architecture
- [x] New config system (.env + YAML + Pydantic)
- [x] Database integration (SQLite + SQLAlchemy)
- [x] Integrated logging system
- [x] Hard link support
- [x] Subtitle subset integration
- [x] Automatic folder watching
- [x] WebUI for task management and monitored folders

### Todo
- [ ] OVA support
- [ ] Improve WebUI design and layout
  - [ ] Refine dashboard design (task table, gallery view)
  - [ ] Improve form interactions and error messages
  - [ ] Add responsive layout for mobile and tablet
  - [ ] Add theme / color customization
- [ ] Recursive handling for nested folders  
- [ ] Jellyfin / Plex integration toggle  
- [ ] RESTful API for external tools


## Usage

```shell
# CLI mode (one-time execution)
python main.py [options] <input_folder> [output_folder]

# Options
  -h, --help        Show help message and exit
  --dryrun          Perform a trial run without making changes
  --verbose         Enable detailed logging output
  --move            Move original folder to archive after sorting

# Web mode (service)
uvicorn ani_sort.web.api:app --reload --port 8000
```

## Configuration
```
# .env
TMDB_API_KEY=your_api_key
AI_API_KEY=optional_ai_key
```

```yaml
# config/settings.yaml
general:
  default_output: "./sorted"
  original_archive_dir: "./orig_archive"
  ...
```


---


## AniSort

这是一个批量 **整理番剧文件** 的工具，通过正则表达式进行匹配

整理逻辑参考 [mikusa的媒体库管理方案](https://www.himiku.com/archives/how-i-organize-my-animation-library.html)


## 整理流程

首先通过 **TMDB API** 与 **原文件夹的名称** 获取番剧信息

再根据元数据对可识别的文件进行格式化重命名

然后采用 PLEX 推荐的分类标准进行分类：

| 文件夹     | 包含内容类型                      |
|------------|------------------------------------|
| Interviews | IV（访谈）                         |
| Trailers   | PV / CM / SPOT / Teaser / Trailer  |
| Other      | Menu / NCOP / NCED 等              |

最后会将所有文件移动到 **新文件夹** 内

并且会在 **新文件夹** 内生成 **Comparison_Table.txt**

该文本内写入了所有文件更改前后的名称，可以对照是否有识别错误

```txt
Season 01/title (2018) - S01E01.mkv
└── [xxx]title - 01.mkv

Season 01/title (2018) - S01E02.mkv
└── [xxx]title - S01E02.mkv
```

对于无法识别的文件，将丢到 `Unknown_Files` 目录

## 效果

* 整理前
```bash
[xxx]title/
├── CDs/
│   ├── [xxx]title - CD.mkv
│   └── [xxx]title - CD2.mkv
├── [xxx]title - CM.mkv
├── [xxx]title - PV.mkv
├── [xxx]title - 01.mkv
└── [xxx]title - S01E02.mkv
```

* 整理后
```bash
title (2018)/
├── Other/
│   ├── title (2018) - S01_CD01.mkv
│   └── title (2018) - S01_CD02.mkv
├── Trailers/
│   ├── title (2018) - S01_广告01.mkv
│   └── title (2018) - S01_宣传片01.mkv
├── Season 01/
│   └── title (2018) - S01E01.mkv
└── └── title (2018) - S01E02.mkv
└── Comparison_Table.txt
```

