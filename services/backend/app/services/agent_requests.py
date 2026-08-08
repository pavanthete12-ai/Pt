from app.services.intent import IntentResult


class AgentRequestFactory:
    def build_agent_type(self, intent: IntentResult) -> str:
        mapping = {
            'file_operation': 'file-agent',
            'research': 'browser-agent',
            'memory_management': 'memory-agent',
            'task_planning': 'planner-agent',
            'general_command': 'core-agent'
        }
        return mapping.get(intent.name, 'core-agent')

    def build_instruction(self, command: str, intent: IntentResult) -> str:
        return f'Analyze and prepare execution plan for intent `{intent.name}`: {command}'
