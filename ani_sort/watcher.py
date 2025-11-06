from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pathlib import Path
import time
import threading


class FolderWatcher(FileSystemEventHandler):
    def __init__(self, watch_path, callback):
        self.watch_path = Path(watch_path).resolve()
        self.callback = callback

    def is_top_level_folder(self, path):
        try:
            relative = path.relative_to(self.watch_path)
            return len(relative.parts) == 1
        except ValueError:
            return False

    def on_created(self, event):
        if event.is_directory:
            created_path = Path(event.src_path).resolve()
            if self.is_top_level_folder(created_path):
                print(f"[Watcher] Folder created/moved into watched/: {created_path}")
                self.callback(created_path)

    def on_moved(self, event):
        dest_path = Path(event.dest_path).resolve()
        if event.is_directory and self.is_top_level_folder(dest_path):
            print(f"[Watcher] Folder moved into watched/: {dest_path}")
            self.callback(dest_path)

    def on_deleted(self, event):
        if event.is_directory and self.is_top_level_folder(Path(event.src_path)):
            print(f"[Watcher] Folder deleted from watched/: {event.src_path}")
            # self.callback_deleted(Path(event.src_path))


def start_watcher(path, callback):
    observer = Observer()
    handler = FolderWatcher(path, callback)

    print(f"[Watcher] Performing initial scan for existing folders in {path}")
    for folder in path.iterdir():
        if folder.is_dir():
            print(f"[Watcher] Found existing folder: {folder}")
            callback(folder)

    observer.schedule(handler, str(path), recursive=True)
    observer_thread = threading.Thread(target=observer.start, daemon=True)
    observer_thread.start()
    print(f"[Watcher] Start Monitoring folder: {path}")

    return observer


# 1.	启动时对每个 library 路径执行一次全量扫描；
# 2.	注册 watcher 监听“文件新增/修改/删除”；
# 3.	若 watcher 出错，退回定时扫描；
# 4.	删除检测：当触发 on_deleted 事件时，立即在 DB 中标记该媒体条目为“missing”。
