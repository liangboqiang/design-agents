from __future__ import annotations

import json
import threading
import time

from design_agents.capabilities.base import Capability
from design_agents.core.models import ActionSpec
from design_agents.core.storage import JsonStore, JsonlStore


class TeamCapability(Capability):
    capability_name = "team"

    def bind(self, engine) -> None:
        super().bind(engine)
        self.roster = JsonStore(engine.paths.state_dir / "team_roster.json")
        if not self.roster.path.exists():
            self.roster.write({"members": []})
        self.threads = {}

    def action_specs(self):
        return [
            ActionSpec("team.spawn_worker", "Spawn worker engine", "创建一个员工智能体；员工与子智能体复用同一 Engine 逻辑。", {"type": "object", "properties": {"name": {"type": "string"}, "skill": {"type": "string"}, "prompt": {"type": "string"}, "enhancements": {"type": "array"}}, "required": ["name", "skill", "prompt"]}, lambda args: self.spawn_worker(args["name"], args["skill"], args["prompt"], [str(item) for item in args.get("enhancements") or self.engine.enhancement_names]), "capability.team"),
            ActionSpec("team.list_workers", "List workers", "查看员工智能体名册。", {"type": "object", "properties": {}}, lambda args: json.dumps(self.roster.read({"members": []}), ensure_ascii=False, indent=2), "capability.team"),
            ActionSpec("team.send_message", "Send worker message", "向某个员工智能体写入消息。", {"type": "object", "properties": {"to": {"type": "string"}, "content": {"type": "string"}}, "required": ["to", "content"]}, lambda args: self.send_message(args["to"], args["content"]), "capability.team"),
            ActionSpec("team.read_inbox", "Read lead inbox", "读取主控收件箱。", {"type": "object", "properties": {}}, lambda args: self.read_inbox("lead"), "capability.team"),
            ActionSpec("team.broadcast", "Broadcast message", "向所有员工广播消息。", {"type": "object", "properties": {"content": {"type": "string"}}, "required": ["content"]}, lambda args: self.broadcast(args["content"]), "capability.team"),
        ]

    def _members(self):
        return list(self.roster.read({"members": []})["members"])

    def _save_members(self, rows):
        self.roster.write({"members": rows})

    def _inbox_store(self, name: str):
        return JsonlStore(self.engine.paths.inbox_dir / f"{name}.jsonl")

    def send_message(self, to: str, content: str, message_type: str = "message", extra: dict | None = None) -> str:
        payload = {"type": message_type, "from": self.engine.engine_id, "content": content, "ts": time.time()}
        if extra:
            payload.update(extra)
        self._inbox_store(to).append(payload)
        return f"sent to {to}"

    def read_inbox(self, name: str) -> str:
        store = self._inbox_store(name)
        rows = store.read_all()
        store.replace([])
        return json.dumps(rows, ensure_ascii=False, indent=2)

    def broadcast(self, content: str) -> str:
        for member in self._members():
            self.send_message(member["name"], content, message_type="broadcast")
        return "broadcast sent"

    def spawn_worker(self, name: str, skill: str, prompt: str, enhancements: list[str]) -> str:
        members = self._members()
        if any(item["name"] == name for item in members):
            raise ValueError(f"Worker already exists: {name}")
        members.append({"name": name, "skill": skill, "status": "working", "enhancements": enhancements})
        self._save_members(members)
        worker = self.engine.spawn_child(skill=skill, enhancements=enhancements, role_name=name, persistent_worker=True)
        thread = threading.Thread(target=self._worker_loop, args=(worker, name, prompt), daemon=True)
        thread.start()
        self.threads[name] = thread
        return f"worker {name} spawned"

    def _worker_loop(self, worker, name: str, prompt: str) -> None:
        worker.chat(prompt)
        while True:
            inbox_rows = json.loads(self.read_inbox(name))
            if inbox_rows:
                for row in inbox_rows:
                    response = worker.chat(row["content"])
                    self._inbox_store("lead").append({"type": "worker_response", "from": name, "content": response, "ts": time.time()})
            elif "autonomy" in worker.enhancement_names:
                worker.process_autonomy_tick()
                time.sleep(1.5)
            else:
                time.sleep(1.5)

    def before_user_turn(self, message: str) -> None:
        lead_messages = self._inbox_store("lead").read_all()
        if lead_messages:
            self.engine.history.append_system(f"<team_inbox>\n{json.dumps(lead_messages, ensure_ascii=False, indent=2)}\n</team_inbox>")
            self._inbox_store("lead").replace([])

    def state_fragments(self) -> list[str]:
        members = self._members()
        if not members:
            return ["team: (no workers)"]
        return ["team:\n" + "\n".join(f"- {m['name']} | skill={m['skill']} | status={m['status']}" for m in members)]
