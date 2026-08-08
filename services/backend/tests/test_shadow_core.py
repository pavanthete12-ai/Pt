from fastapi.testclient import TestClient

from app.main import app


def test_shadow_core_receives_command_and_creates_task() -> None:
    with TestClient(app) as client:
        response = client.post('/api/v1/core/commands', json={'command': 'Research local-first memory systems'})

    assert response.status_code == 202
    body = response.json()
    assert body['task']['id'].startswith('task_')
    assert body['task']['conversation_id'].startswith('conv_')
    assert body['task']['intent'] == 'research'
    assert body['task']['status'] == 'awaiting_agent'
    assert body['task']['agent_requests'][0]['agent_type'] == 'browser-agent'
    assert 'generate_agent_request' in body['response_pipeline']
    assert any(log['event'] == 'response_pipeline_generated' for log in body['task']['logs'])
