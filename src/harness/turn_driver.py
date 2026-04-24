from __future__ import annotations

from .turn_guard import ActionExecutionResult


class TurnDriver:
    def __init__(self, ports):  # noqa: ANN001
        self.ports = ports

    def chat(self, message: str, files: list[dict] | None = None) -> str:
        begin = self.ports.fault_boundary.call(
            phase="turn_begin",
            source_type="harness",
            source_name="TurnDriver._begin_turn",
            fn=lambda: self._begin_turn(message, files),
            context={"attachments": len(files or [])},
        )
        if not begin.ok:
            return self._visible_fault_message(begin.fault, fallback="")
        return self._run_turn_loop()

    def _begin_turn(self, message: str, files: list[dict] | None) -> None:
        self.ports.lifecycle.before_user_turn(message, files=files)
        self.ports.events.emit(
            "user.turn.started",
            message=message,
            active_skill=self.ports.skill_state.active_skill_id,
            attachments=len(files or []),
        )
        self.ports.session.history.append_user(message, files=files)

    def _run_turn_loop(self) -> str:
        final_answer = ""
        for step in range(self.ports.settings.max_steps):
            self.ports.lifecycle.before_model_call()
            self.ports.events.emit("model.turn.prep", step=step)

            state_fragments = self.ports.lifecycle.state_fragments()

            surface_guard = self.ports.fault_boundary.call(
                phase="surface_compile",
                source_type="harness",
                source_name="surface_assembler.assemble_surface",
                fn=lambda: self._assemble_surface(state_fragments),
            )
            if not surface_guard.ok:
                return self._visible_fault_message(surface_guard.fault, fallback=final_answer)
            surface = surface_guard.value

            prompt_guard = self.ports.fault_boundary.call(
                phase="prompt_build",
                source_type="harness",
                source_name="prompt_assembler.build_system_prompt",
                fn=lambda: self._build_system_prompt(surface, state_fragments),
            )
            if not prompt_guard.ok:
                return self._visible_fault_message(prompt_guard.fault, fallback=final_answer)
            system_prompt = prompt_guard.value

            messages_guard = self.ports.fault_boundary.call(
                phase="message_build",
                source_type="harness",
                source_name="prompt_assembler.build_messages",
                fn=lambda: self.ports.prompt_assembler.build_messages(
                    self.ports.session.history.read(),
                    self.ports.settings.history_keep_turns,
                ),
            )
            if not messages_guard.ok:
                return self._visible_fault_message(messages_guard.fault, fallback=final_answer)
            messages = messages_guard.value

            llm_guard = self.ports.fault_boundary.call(
                phase="llm_complete",
                source_type="llm",
                source_name=self.ports.settings.model,
                fn=lambda: self.ports.llm.complete(system_prompt, messages),
            )
            if not llm_guard.ok:
                return self._visible_fault_message(llm_guard.fault, fallback=final_answer)
            raw = llm_guard.value

            parse_guard = self.ports.fault_boundary.call(
                phase="response_parse",
                source_type="parser",
                source_name="reply_parser.parse",
                fn=lambda: self.ports.reply_parser.parse(raw),
                context={"raw_preview": str(raw)[:1000]},
            )
            if not parse_guard.ok:
                return self._visible_fault_message(parse_guard.fault, fallback=final_answer)
            parsed = parse_guard.value
            self.ports.audit.record("llm.response", raw=raw, tool_calls=len(parsed.tool_calls))

            if parsed.assistant_message:
                self.ports.session.history.append_assistant(parsed.assistant_message)
                final_answer = parsed.assistant_message

            if not parsed.tool_calls:
                self.ports.events.emit("model.turn.completed", final_answer=final_answer)
                return final_answer or ""

            final_answer = self._handle_tool_calls(parsed.tool_calls, fallback=final_answer)
        return final_answer or "Max steps reached."

    def _assemble_surface(self, state_fragments: list[str]):
        surface = self.ports.surface_assembler.assemble_surface(
            skill_state=self.ports.skill_state,
            action_registry=self.ports.action_registry,
            state_fragments=state_fragments,
            recent_events=self.ports.events.recent(),
        )
        self.ports.state.last_surface_snapshot = surface
        return surface

    def _build_system_prompt(self, surface, state_fragments: list[str]):  # noqa: ANN001
        selection = self.ports.knowledge_picker.pick(surface_snapshot=surface, knowledge_hub=self.ports.knowledge_hub)
        return self.ports.prompt_assembler.build_system_prompt(
            engine_context=self.ports.context,
            skill_state=self.ports.skill_state,
            surface_snapshot=surface,
            history_rows=self.ports.session.history.read(),
            state_fragments=state_fragments,
            recent_events=self.ports.events.recent(),
            audit=self.ports.audit,
            registry=self.ports.registry,
            knowledge_brief=selection.brief,
            knowledge_actions_visible=selection.actions_visible,
        )

    def _handle_tool_calls(self, tool_calls, *, fallback: str):  # noqa: ANN001
        final_answer = fallback
        for call in tool_calls:
            dispatch_guard = self.ports.fault_boundary.call(
                phase="tool_dispatch_guard",
                source_type="harness",
                source_name=call.action,
                fn=lambda: self.ports.dispatcher.dispatch(call.action, call.arguments),
                context={"action": call.action, "arguments": call.arguments},
            )
            if dispatch_guard.ok and isinstance(dispatch_guard.value, ActionExecutionResult):
                execution = dispatch_guard.value
            elif dispatch_guard.ok:
                execution = ActionExecutionResult.from_value(call.action, dispatch_guard.value)
            else:
                execution = ActionExecutionResult.from_fault(call.action, dispatch_guard.fault)

            normalize_guard = self.ports.fault_boundary.call(
                phase="tool_normalize",
                source_type="normalizer",
                source_name=call.action,
                fn=lambda: self.ports.normalizer.normalize_tool_result(call.action, execution.content, limit=8_000),
                context={"action": call.action, "trace_id": execution.trace_id},
            )
            normalized_result = (
                normalize_guard.value
                if normalize_guard.ok
                else self._visible_fault_message(normalize_guard.fault, fallback=execution.content)
            )

            self.ports.session.history.append_tool(call.action, normalized_result)
            event_name = "tool.result" if execution.ok else "tool.error"
            self.ports.events.emit(
                event_name,
                action=call.action,
                result=normalized_result,
                trace_id=execution.trace_id,
            )
            self.ports.lifecycle.after_tool_call(call.action, normalized_result)
            final_answer = normalized_result
        return final_answer

    def _visible_fault_message(self, fault, *, fallback: str) -> str:  # noqa: ANN001
        if fault is None:
            return fallback or "Runtime failure."
        message = fault.user_message()
        try:
            self.ports.session.history.append_system(message)
        except Exception:
            pass
        return fallback or message
