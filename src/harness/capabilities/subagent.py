from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, as_completed

from schemas.action import ActionSpec

from .base import Capability


class SubagentCapability(Capability):
    capability_name = "subagent"

    def action_specs(self):
        return [
            ActionSpec(
                "subagent.ask",
                "Delegate to subagent",
                "Instantiate one child engine from the current parent engine and return the child result.",
                {
                    "type": "object",
                    "properties": {
                        "prompt": {"type": "string"},
                        "skill": {"type": "string"},
                        "enhancements": {"type": "array"},
                        "toolboxes": {"type": "array"},
                        "role_name": {"type": "string"},
                    },
                    "required": ["prompt"],
                },
                lambda args: self.ask(
                    prompt=str(args["prompt"]),
                    skill=args.get("skill"),
                    enhancements=[str(item) for item in args.get("enhancements") or []],
                    toolboxes=[str(item) for item in args.get("toolboxes") or []]
                    if args.get("toolboxes") is not None
                    else None,
                    role_name=str(args.get("role_name") or "subagent"),
                ),
                "capability.subagent",
            ),
            ActionSpec(
                "subagent.batch_run",
                "Batch run subagents",
                "Instantiate multiple child engines in parallel and run one prompt per child.",
                {
                    "type": "object",
                    "properties": {
                        "jobs": {"type": "array"},
                        "max_workers": {"type": "integer"},
                    },
                    "required": ["jobs"],
                },
                lambda args: self.batch_run(
                    jobs=[dict(item) for item in args.get("jobs") or []],
                    max_workers=int(args.get("max_workers") or 4),
                ),
                "capability.subagent",
            ),
        ]

    def ask(
        self,
        *,
        prompt: str,
        skill: str | None,
        enhancements: list[str],
        toolboxes: list[str] | None,
        role_name: str,
    ) -> str:
        child = self.engine.spawn_child(
            skill=skill,
            enhancements=enhancements or self.engine.enhancement_names,
            role_name=role_name,
            toolboxes=toolboxes,
        )
        return child.chat(prompt)

    def batch_run(self, *, jobs: list[dict], max_workers: int = 4) -> str:
        if not jobs:
            return json.dumps({"status": "ok", "results": []}, ensure_ascii=False, indent=2)

        max_workers = max(1, min(int(max_workers or 4), len(jobs), 16))
        results: list[dict | None] = [None] * len(jobs)

        def run_one(index: int, job: dict) -> dict:
            role_name = str(job.get("role_name") or f"subagent_{index + 1:03d}")
            try:
                result = self.ask(
                    prompt=str(job["prompt"]),
                    skill=job.get("skill"),
                    enhancements=[str(item) for item in job.get("enhancements") or self.engine.enhancement_names],
                    toolboxes=[str(item) for item in job.get("toolboxes") or []]
                    if job.get("toolboxes") is not None
                    else None,
                    role_name=role_name,
                )
                return {
                    "index": index,
                    "role_name": role_name,
                    "skill": str(job.get("skill") or ""),
                    "ok": True,
                    "result": result,
                }
            except Exception as exc:  # noqa: BLE001
                return {
                    "index": index,
                    "role_name": role_name,
                    "skill": str(job.get("skill") or ""),
                    "ok": False,
                    "error": f"{type(exc).__name__}: {exc}",
                }

        with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="subagent_batch") as pool:
            futures = {pool.submit(run_one, index, job): index for index, job in enumerate(jobs)}
            for future in as_completed(futures):
                payload = future.result()
                results[payload["index"]] = payload

        return json.dumps(
            {
                "status": "ok",
                "max_workers": max_workers,
                "results": results,
            },
            ensure_ascii=False,
            indent=2,
        )
