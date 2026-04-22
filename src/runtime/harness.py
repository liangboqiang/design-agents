from __future__ import annotations


class Harness:
    def __init__(self, ports):  # noqa: ANN001
        self.ports = ports

    def chat(self, message: str, files: list[dict] | None = None) -> str:
        self._begin_turn(message, files)
        return self._run_turn_loop()

    def _begin_turn(self, message: str, files: list[dict] | None) -> None:
        self.ports.lifecycle.before_user_turn(message, files=files)
        self.ports.events.emit(
            "user.turn.started",
            message=message,
            active_skill=self.ports.skill_runtime.active_skill_id,
            attachments=len(files or []),
        )
        self.ports.session.history.append_user(message, files=files)

    def _run_turn_loop(self) -> str:
        final_answer = ""
        for step in range(self.ports.settings.max_steps):
            self.ports.lifecycle.before_model_call()
            self.ports.events.emit("model.turn.prep", step=step)

            state_fragments = self.ports.lifecycle.state_fragments()
            surface = self._compile_surface(state_fragments)
            system_prompt = self._build_system_prompt(surface, state_fragments)
            messages = self.ports.context_assembler.build_messages(
                self.ports.session.history.read(),
                self.ports.settings.history_keep_turns,
            )

            raw = self.ports.llm.complete(system_prompt, messages)
            parsed = self.ports.response_parser.parse(raw)
            self.ports.audit.record("llm.response", raw=raw, tool_calls=len(parsed.tool_calls))

            if parsed.assistant_message:
                self.ports.session.history.append_assistant(parsed.assistant_message)
                final_answer = parsed.assistant_message

            if not parsed.tool_calls:
                self.ports.events.emit("model.turn.completed", final_answer=final_answer)
                return final_answer or ""

            final_answer = self._handle_tool_calls(parsed.tool_calls, fallback=final_answer)
        return final_answer or "Max steps reached."

    def _compile_surface(self, state_fragments: list[str]):
        surface = self.ports.surface_resolver.resolve(
            skill_runtime=self.ports.skill_runtime,
            action_registry=self.ports.action_registry,
            state_fragments=state_fragments,
            recent_events=self.ports.events.recent(),
        )
        self.ports.state.last_surface_snapshot = surface
        return surface

    def _build_system_prompt(self, surface, state_fragments: list[str]):  # noqa: ANN001
        knowledge_actions_visible = any(spec.action_id.startswith("wiki.") for spec in surface.visible_actions)
        knowledge_brief = self.ports.knowledge_hub.system_brief() if knowledge_actions_visible else None
        return self.ports.context_assembler.build_system_prompt(
            engine_context=self.ports.context,
            skill_runtime=self.ports.skill_runtime,
            surface_snapshot=surface,
            history_rows=self.ports.session.history.read(),
            state_fragments=state_fragments,
            recent_events=self.ports.events.recent(),
            audit=self.ports.audit,
            registry=self.ports.registry,
            knowledge_brief=knowledge_brief,
            knowledge_actions_visible=knowledge_actions_visible,
        )

    def _handle_tool_calls(self, tool_calls, *, fallback: str):  # noqa: ANN001
        final_answer = fallback
        for call in tool_calls:
            result = self.ports.dispatcher.dispatch(call.action, call.arguments)
            normalized_result = self.ports.normalizer.normalize_tool_result(call.action, result, limit=8_000)
            self.ports.session.history.append_tool(call.action, normalized_result)
            event_name = "tool.error" if isinstance(result, str) and result.startswith("Error") else "tool.result"
            self.ports.events.emit(event_name, action=call.action, result=result)
            self.ports.lifecycle.after_tool_call(call.action, result)
            final_answer = result
        return final_answer
