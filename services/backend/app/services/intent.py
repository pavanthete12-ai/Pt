from dataclasses import dataclass


@dataclass(frozen=True)
class IntentResult:
    name: str
    confidence: float
    summary: str


class IntentAnalyzer:
    def analyze(self, command: str) -> IntentResult:
        normalized = command.lower()
        if any(keyword in normalized for keyword in ('file', 'folder', 'document', 'open')):
            return IntentResult('file_operation', 0.74, 'User appears to be requesting file or document work.')
        if any(keyword in normalized for keyword in ('search', 'browse', 'research', 'web')):
            return IntentResult('research', 0.78, 'User appears to be requesting research or browsing work.')
        if any(keyword in normalized for keyword in ('remember', 'memory', 'recall', 'knowledge')):
            return IntentResult('memory_management', 0.72, 'User appears to be requesting memory or knowledge work.')
        if any(keyword in normalized for keyword in ('plan', 'build', 'create', 'generate', 'design')):
            return IntentResult('task_planning', 0.81, 'User appears to be requesting planning or creation work.')
        return IntentResult('general_command', 0.62, 'User command requires general reasoning before routing.')
