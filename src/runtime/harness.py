from __future__ import annotations


class Harness:
    def __init__(self, engine):  # noqa: ANN001
        self.engine = engine

    def chat(self, message: str) -> str:
        self.engine.lifecycle.before_user_turn(message)
        self.engine.events.emit(
            "user.turn.started",
            message=message,
            active_skill=self.engine.skill_runtime.active_skill_id,
        )

        self.engine.session.history.append_user(message)
        final_answer = ""

        for step in range(self.engine.settings.max_steps):
            self.engine.lifecycle.before_model_call()
            self.engine.events.emit("model.turn.prep", step=step)

            state_fragments = self.engine.lifecycle.state_fragments()
            surface = self.engine.action_compiler.compile_surface(
                skill_runtime=self.engine.skill_runtime,
                action_registry=self.engine.action_registry,
                state_fragments=state_fragments,
                recent_events=self.engine.events.recent(),
            )
            self.engine.last_surface_snapshot = surface
            system_prompt = self.engine.context_assembler.build_system_prompt(
                engine_context=self.engine.context,
                skill_runtime=self.engine.skill_runtime,
                surface_snapshot=surface,
                history_rows=self.engine.session.history.read(),
                state_fragments=state_fragments,
                recent_events=self.engine.events.recent(),
                audit=self.engine.audit,
                registry=self.engine.registry,
            )
            messages = self.engine.context_assembler.build_messages(
                self.engine.session.history.read(),
                self.engine.settings.history_keep_turns,
            )

            raw = self.engine.llm.complete(system_prompt, messages)
            parsed = self.engine.response_parser.parse(raw)
            self.engine.audit.record("llm.response", raw=raw, tool_calls=len(parsed.tool_calls))

            if parsed.assistant_message:
                self.engine.session.history.append_assistant(parsed.assistant_message)
                final_answer = parsed.assistant_message

            if not parsed.tool_calls:
                self.engine.events.emit("model.turn.completed", final_answer=final_answer)
                return final_answer or ""

            for call in parsed.tool_calls:
                result = self.engine.dispatcher.dispatch(call.action, call.arguments)
                normalized_result = self.engine.normalizer.normalize_tool_result(call.action, result, limit=8_000)
                self.engine.append_tool_result(call.action, normalized_result)
                event_name = "tool.error" if result.startswith("Error") else "tool.result"
                self.engine.events.emit(event_name, action=call.action, result=result)
                self.engine.lifecycle.after_tool_call(call.action, result)
                final_answer = result

        return final_answer or "Max steps reached."

