from __future__ import annotations

import json
import threading
import time

from schemas.action import ActionSpec

from .base import Capability


class TeamCapability(Capability):
    capability_name = "team"
    roster_file = "team_roster.json"

    def bind(self, runtime, capability_lookup=None) -> None:
        super().bind(runtime, capability_lookup)
        if self.runtime.session.read_state_json(self.roster_file, None) is None:
            self.runtime.session.write_state_json(self.roster_file, {"members": []})
        self.threads: dict[str, threading.Thread] = {}

    def action_specs(self):
        return [
            ActionSpec(
                "team.spawn_worker",
                "Spawn worker runtime",
                "Create a worker agent that reuses the same runtime framework.",
                {
                    "type": "object",
                    "properties": {"name": {"type": "string"}, "skill": {"type": "string"}, "prompt": {"type": "string"}, "enhancements": {"type": "array"}},
                    "required": ["name", "skill", "prompt"],
                },
                lambda args: self.spawn_worker(
                    args["name"],
                    args["skill"],
                    args["prompt"],
                    [str(item) for item in args.get("enhancements") or self.runtime.enhancement_names],
                ),
                "capability.team",
            ),
            ActionSpec(
                "team.list_workers",
                "List workers",
                "List registered workers.",
                {"type": "object", "properties": {}},
                lambda args: json.dumps(self._roster(), ensure_ascii=False, indent=2),
                "capability.team",
            ),
            ActionSpec(
                "team.send_message",
                "Send worker message",
                "Send a message to a worker inbox.",
                {
                    "type": "object",
                    "properties": {"to": {"type": "string"}, "content": {"type": "string"}},
                    "required": ["to", "content"],
                },
                lambda args: self.send_message(args["to"], args["content"]),
                "capability.team",
            ),
            ActionSpec(
                "team.read_inbox",
                "Read lead inbox",
                "Read the lead inbox.",
                {"type": "object", "properties": {}},
                lambda args: self.read_inbox("lead"),
                "capability.team",
            ),
            ActionSpec(
                "team.broadcast",
                "Broadcast message",
                "Broadcast a message to all workers.",
                {"type": "object", "properties": {"content": {"type": "string"}}, "required": ["content"]},
                lambda args: self.broadcast(args["content"]),
                "capability.team",
            ),
        ]

    def _roster(self) -> list[dict]:
        return list(self.runtime.session.read_state_json(self.roster_file, {"members": []})["members"])

    def _save_roster(self, rows: list[dict]) -> None:
        self.runtime.session.write_state_json(self.roster_file, {"members": rows})

    def send_message(self, to: str, content: str, message_type: str = "message", extra: dict | None = None) -> str:
        payload = {"type": message_type, "from": self.runtime.engine_id, "content": content, "ts": time.time()}
        if extra:
            payload.update(extra)
        self.runtime.session.inbox.append(to, payload)
        return f"sent to {to}"

    def read_inbox(self, name: str) -> str:
        rows = self.runtime.session.inbox.drain(name)
        return json.dumps(rows, ensure_ascii=False, indent=2)

    def broadcast(self, content: str) -> str:
        for member in self._roster():
            self.send_message(member["name"], content, message_type="broadcast")
        return "broadcast sent"

    def spawn_worker(self, name: str, skill: str, prompt: str, enhancements: list[str]) -> str:
        members = self._roster()
        if any(item["name"] == name for item in members):
            raise ValueError(f"Worker already exists: {name}")
        members.append({"name": name, "skill": skill, "status": "working", "enhancements": enhancements})
        self._save_roster(members)
        worker = self.runtime.spawn_child(skill=skill, enhancements=enhancements, role_name=name)
        thread = threading.Thread(target=self._worker_loop, args=(worker, name, prompt, "autonomy" in enhancements), daemon=True)
        thread.start()
        self.threads[name] = thread
        self.runtime.events.emit("team.worker_spawned", worker=name, skill=skill)
        return f"worker {name} spawned"

    def _worker_loop(self, worker, name: str, prompt: str, has_autonomy: bool) -> None:  # noqa: ANN001
        worker.chat(prompt)
        while True:
            inbox_rows = self.runtime.session.inbox.drain(name)
            if inbox_rows:
                for row in inbox_rows:
                    response = worker.chat(row["content"])
                    self.runtime.session.inbox.append("lead", {"type": "worker_response", "from": name, "content": response, "ts": time.time()})
            elif has_autonomy:
                worker.tick()
                time.sleep(1.5)
            else:
                time.sleep(1.5)

    def before_user_turn(self, message: str) -> None:
        lead_messages = self.runtime.session.inbox.read_all("lead")
        if lead_messages:
            self.runtime.session.history.append_system(
                f"<team_inbox>\n{json.dumps(lead_messages, ensure_ascii=False, indent=2)}\n</team_inbox>"
            )
            self.runtime.session.inbox.drain("lead")

    def state_fragments(self) -> list[str]:
        members = self._roster()
        if not members:
            return ["team: (no workers)"]
        return ["team:\n" + "\n".join(f"- {m['name']} | skill={m['skill']} | status={m['status']}" for m in members)]
