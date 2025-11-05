from fastapi import FastAPI
from ani_sort.task import run_sort_task

app = FastAPI()


@app.post("/sort")
def sort_anime(input: str, output: str | None = None, dryrun: bool = False):
    return run_sort_task(input, output, dryrun)
