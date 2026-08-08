from app.services.intent import IntentResult


class ResponsePipelineBuilder:
    def build(self, intent: IntentResult) -> list[str]:
        return [
            'validate_command',
            'persist_user_message',
            f'understand_intent:{intent.name}',
            'create_task_object',
            'generate_agent_request',
            'track_execution_status',
            'persist_assistant_response'
        ]
