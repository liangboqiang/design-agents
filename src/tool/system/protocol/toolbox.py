from __future__ import annotations

import json
import time
import uuid

from protocol.types import ToolSpec
from tool.stateful import StatefulToolbox


class ProtocolCapability(StatefulToolbox):
    toolbox_name = "protocol"
    shutdown_file = "shutdown_requests.json"
    plan_file = "plan_requests.json"

    def bind_runtime(self, runtime, tool_lookup=None) -> None:
        super().bind_runtime(runtime, tool_lookup)
        if self.runtime.session.read_state_json(self.shutdown_file, None) is None:
            self.runtime.session.write_state_json(self.shutdown_file, {})
        if self.runtime.session.read_state_json(self.plan_file, None) is None:
            self.runtime.session.write_state_json(self.plan_file, {})

    def tool_specs(self):
        return [
            ToolSpec("protocol.request_shutdown", "Request worker shutdown", "Request graceful worker shutdown.", {"type": "object", "properties": {"worker": {"type": "string"}}, "required": ["worker"]}, lambda args: self.request_shutdown(args["worker"]), self.toolbox_name),
            ToolSpec(
                "protocol.respond_shutdown",
                "Respond shutdown",
                "Approve or reject a shutdown request.",
                {"type": "object", "properties": {"request_id": {"type": "string"}, "approve": {"type": "boolean"}, "reason": {"type": "string"}}, "required": ["request_id", "approve"]},
                lambda args: self.respond_shutdown(args["request_id"], bool(args["approve"]), args.get("reason", "")),
                self.toolbox_name,
            ),
            ToolSpec(
                "protocol.submit_plan",
                "Submit plan",
                "Submit a plan for review.",
                {"type": "object", "properties": {"from_worker": {"type": "string"}, "plan": {"type": "string"}}, "required": ["from_worker", "plan"]},
                lambda args: self.submit_plan(args["from_worker"], args["plan"]),
                self.toolbox_name,
            ),
            ToolSpec(
                "protocol.review_plan",
                "Review plan",
                "Approve or reject a submitted plan.",
                {"type": "object", "properties": {"request_id": {"type": "string"}, "approve": {"type": "boolean"}, "feedback": {"type": "string"}}, "required": ["request_id", "approve"]},
                lambda args: self.review_plan(args["request_id"], bool(args["approve"]), args.get("feedback", "")),
                self.toolbox_name,
            ),
        ]

    def _team(self):
        return self.capability("team")

    def request_shutdown(self, worker: str) -> str:
        req_id = str(uuid.uuid4())[:8]
        payload = self.runtime.session.read_state_json(self.shutdown_file, {})
        payload[req_id] = {"target": worker, "status": "pending", "ts": time.time()}
        self.runtime.session.write_state_json(self.shutdown_file, payload)
        self._team().send_message(worker, "Please shut down gracefully.", message_type="shutdown_request", extra={"request_id": req_id})
        self.runtime.events.emit("protocol.shutdown_requested", request_id=req_id, worker=worker)
        return f"shutdown request {req_id} sent to {worker}"

    def respond_shutdown(self, request_id: str, approve: bool, reason: str) -> str:
        payload = self.runtime.session.read_state_json(self.shutdown_file, {})
        payload.setdefault(request_id, {})
        payload[request_id]["status"] = "approved" if approve else "rejected"
        payload[request_id]["reason"] = reason
        self.runtime.session.write_state_json(self.shutdown_file, payload)
        self._team().send_message("lead", reason or "", message_type="shutdown_response", extra={"request_id": request_id, "approve": approve})
        self.runtime.events.emit("protocol.shutdown_reviewed", request_id=request_id, approve=approve)
        return json.dumps(payload[request_id], ensure_ascii=False, indent=2)

    def submit_plan(self, from_worker: str, plan: str) -> str:
        req_id = str(uuid.uuid4())[:8]
        payload = self.runtime.session.read_state_json(self.plan_file, {})
        payload[req_id] = {"from": from_worker, "plan": plan, "status": "pending", "ts": time.time()}
        self.runtime.session.write_state_json(self.plan_file, payload)
        self._team().send_message("lead", plan, message_type="plan_request", extra={"request_id": req_id, "from_worker": from_worker})
        self.runtime.events.emit("protocol.plan_submitted", request_id=req_id, worker=from_worker)
        return f"plan request {req_id} submitted"

    def review_plan(self, request_id: str, approve: bool, feedback: str) -> str:
        payload = self.runtime.session.read_state_json(self.plan_file, {})
        if request_id not in payload:
            raise ValueError(f"Unknown plan request {request_id}")
        payload[request_id]["status"] = "approved" if approve else "rejected"
        payload[request_id]["feedback"] = feedback
        self.runtime.session.write_state_json(self.plan_file, payload)
        self._team().send_message(payload[request_id]["from"], feedback, message_type="plan_response", extra={"request_id": request_id, "approve": approve})
        self.runtime.events.emit("protocol.plan_reviewed", request_id=request_id, approve=approve)
        return json.dumps(payload[request_id], ensure_ascii=False, indent=2)
