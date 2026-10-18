"""Read-only query of a pre-existing Nano Banana task owned by your Key."""

import argparse

from nano_banana_crewai import NanoBananaRetrieveTaskTool

p = argparse.ArgumentParser(description=__doc__)
p.add_argument("task_id")
a = p.parse_args()
print(NanoBananaRetrieveTaskTool().run(task_id=a.task_id, wait_seconds=0))
