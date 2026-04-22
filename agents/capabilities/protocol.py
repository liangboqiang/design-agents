from __future__ import annotations

import json
import time
import uuid

from agents.capabilities.base import Capability
from agents.core.models import ActionSpec
from agents.core.storage import JsonStore


class ProtocolCapability(Capability):
    capability_name = "protocol"

    def bind(self, engine) -> None:
        super().bind(engine)
        self.shutdown_requests = JsonStore(engine.paths.state_dir / "shutdown_requests.json")
        self.plan_requests = JsonStore(engine.paths.state_dir / "plan_requests.json")
        if not self.shutdown_requests.path.exists():
            self.shutdown_requests.write({})
        if not self.plan_requests.path.exists():
            self.plan_requests.write({})

    def action_specs(self):
        return [
            ActionSpec("protocol.request_shutdown", "Request worker shutdown", "向员工发起优雅关闭请求。", {"type": "object", "properties": {"worker": {"type": "string"}}, "required": ["worker"]}, lambda args: self.request_shutdown(args["worker"]), "capability.protocol"),
            ActionSpec("protocol.respond_shutdown", "Respond shutdown", "对关闭请求作出批准或拒绝。", {"type": "object", "properties": {"request_id": {"type": "string"}, "approve": {"type": "boolean"}, "reason": {"type": "string"}}, "required": ["request_id", "approve"]}, lambda args: self.respond_shutdown(args["request_id"], bool(args["approve"]), args.get("reason", "")), "capability.protocol"),
            ActionSpec("protocol.submit_plan", "Submit plan", "员工向 lead 提交计划审查。", {"type": "object", "properties": {"from_worker": {"type": "string"}, "plan": {"type": "string"}}, "required": ["from_worker", "plan"]}, lambda args: self.submit_plan(args["from_worker"], args["plan"]), "capability.protocol"),
            ActionSpec("protocol.review_plan", "Review plan", "主控对计划进行批准或拒绝。", {"type": "object", "properties": {"request_id": {"type": "string"}, "approve": {"type": "boolean"}, "feedback": {"type": "string"}}, "required": ["request_id", "approve"]}, lambda args: self.review_plan(args["request_id"], bool(args["approve"]), args.get("feedback", "")), "capability.protocol"),
        ]

    def _team(self):
        return self.engine.capability("team")

    def request_shutdown(self, worker: str) -> str:
        req_id = str(uuid.uuid4())[:8]
        payload = self.shutdown_requests.read({})
        payload[req_id] = {"target": worker, "status": "pending", "ts": time.time()}
        self.shutdown_requests.write(payload)
        self._team().send_message(worker, "Please shut down gracefully.", message_type="shutdown_request", extra={"request_id": req_id})
        return f"shutdown request {req_id} sent to {worker}"

    def respond_shutdown(self, request_id: str, approve: bool, reason: str) -> str:
        payload = self.shutdown_requests.read({})
        payload.setdefault(request_id, {})
        payload[request_id]["status"] = "approved" if approve else "rejected"
        payload[request_id]["reason"] = reason
        self.shutdown_requests.write(payload)
        self._team().send_message("lead", reason or "", message_type="shutdown_response", extra={"request_id": request_id, "approve": approve})
        return json.dumps(payload[request_id], ensure_ascii=False, indent=2)

    def submit_plan(self, from_worker: str, plan: str) -> str:
        req_id = str(uuid.uuid4())[:8]
        payload = self.plan_requests.read({})
        payload[req_id] = {"from": from_worker, "plan": plan, "status": "pending", "ts": time.time()}
        self.plan_requests.write(payload)
        self._team().send_message("lead", plan, message_type="plan_request", extra={"request_id": req_id, "from_worker": from_worker})
        return f"plan request {req_id} submitted"

    def review_plan(self, request_id: str, approve: bool, feedback: str) -> str:
        payload = self.plan_requests.read({})
        if request_id not in payload:
            raise ValueError(f"Unknown plan request {request_id}")
        payload[request_id]["status"] = "approved" if approve else "rejected"
        payload[request_id]["feedback"] = feedback
        self.plan_requests.write(payload)
        self._team().send_message(payload[request_id]["from"], feedback, message_type="plan_response", extra={"request_id": request_id, "approve": approve})
        return json.dumps(payload[request_id], ensure_ascii=False, indent=2)
