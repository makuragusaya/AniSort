import subprocess
import shutil
from pathlib import Path
import logging


def run_cmd(cmd, logger, cwd=None):
    """运行命令并捕获输出，如果包含 [ERROR] 或非零退出码则返回 False。"""
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        cwd=cwd,
    )
    output = result.stdout
    if "[ERROR]" in output or result.returncode != 0:
        logger.error(f"Command failed: {' '.join(cmd)}")
        logger.error(output)
        return False
    logger.debug(output)
    return True


def subset_ass_fonts(target_dir: str | Path, logger: logging.Logger | None = None):
    """
    对目标文件夹内的所有 ASS 文件执行字体子集化和嵌入操作。
    要求系统安装 assfonts & otf2ttf。
    """
    logger = logger or logging.getLogger("AniSort")
    target_dir = Path(target_dir)

    if not target_dir.exists() or not target_dir.is_dir():
        logger.error(f"目标路径无效: {target_dir}")
        return

    # 检查依赖
    if not shutil.which("assfonts"):
        logger.error("assfonts 未安装或不在 PATH 中。请先安装。")
        return
    if not shutil.which("otf2ttf"):
        logger.warning("otf2ttf 未安装，将跳过 OTF→TTF 转换。")

    logger.info("--- 开始递归处理 ASS 文件 ---")
    logger.info(f"目标目录: {target_dir}")

    ignore_dirs = {"old_sub", "subsetted"}
    ass_files = [
        f
        for f in target_dir.rglob("*.ass")
        if not any(p.name in ignore_dirs for p in f.parents)
    ]

    for ass_file in ass_files:
        logger.info("=" * 50)
        logger.info(f"处理文件: {ass_file}")

        subset_dir = ass_file.parent / f"{ass_file.stem}_subsetted"
        backup_dir = ass_file.parent / "old_sub"

        # 清理并准备输出目录
        if subset_dir.exists():
            shutil.rmtree(subset_dir)
        subset_dir.mkdir(exist_ok=True)
        backup_dir.mkdir(exist_ok=True)

        # Step 1: 抽取字体
        logger.info(f"1. 抽取并子集化字体到 {subset_dir}")
        if not run_cmd(
            ["assfonts", "-o", str(subset_dir), "-s", "-i", str(ass_file)], logger
        ):
            logger.warning(f"跳过该文件，因字体子集化失败: {ass_file}")
            shutil.rmtree(subset_dir, ignore_errors=True)
            continue

        # Step 2: 转换 OTF → TTF（如果 otf2ttf 可用）
        otf_files = list(subset_dir.glob("*.otf"))
        if otf_files and shutil.which("otf2ttf"):
            logger.info("2. 检测到 OTF 字体，转换为 TTF...")
            subprocess.run(["otf2ttf", *map(str, otf_files)], check=False)

        # Step 3: 嵌入子集字体
        logger.info("3. 将子集化字体嵌入到 ASS 文件中...")
        if not run_cmd(
            ["assfonts", "-f", str(subset_dir), "-i", str(ass_file)], logger
        ):
            logger.warning(f"跳过该文件，因嵌入阶段失败: {ass_file}")
            shutil.rmtree(subset_dir, ignore_errors=True)
            continue

        # Step 4: 清理
        logger.info(f"4. 删除临时文件夹 {subset_dir}")
        shutil.rmtree(subset_dir, ignore_errors=True)

        # Step 5: 备份原文件
        logger.info(f"5. 移动原字幕文件到 {backup_dir}")
        shutil.move(str(ass_file), str(backup_dir / ass_file.name))

        logger.info(f"文件处理完成: {ass_file}")

    logger.info("--- 所有 ASS 文件处理完毕 ---")
