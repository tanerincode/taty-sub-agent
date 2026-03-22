from src.core.models import Skill, AgentTask, AgentResult, TaskBatch


def test_skill_model():
    skill = Skill(name="test", description="A test skill", content="You are a tester.")
    assert skill.name == "test"


def test_agent_task_defaults():
    task = AgentTask(task="do something")
    assert task.skill is None
    assert task.store_result is True


def test_agent_result_success():
    result = AgentResult(task="do something", skill_name="test", output="done", success=True)
    assert result.success
    assert result.error is None


def test_task_batch():
    tasks = [AgentTask(task=f"task {i}") for i in range(3)]
    batch = TaskBatch(tasks=tasks, description="test batch")
    assert len(batch.tasks) == 3
