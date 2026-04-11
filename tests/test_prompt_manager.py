import pytest
import yaml

from src.services.prompt_manager import PromptManager


@pytest.fixture
def temp_prompts_dir(tmp_path):
    d = tmp_path / "prompts"
    d.mkdir()

    # Create a test prompt
    prompt_data = {
        "id": "test_prompt",
        "version": "1.0.0",
        "system_prompt": "Hello {{ name }}!",
        "user_prompt_template": "Topic: {{ topic }}",
        "config": {"temperature": 0.5, "max_tokens": 500, "model_name": "gpt-4"},
    }

    with open(d / "test_v1.yaml", "w", encoding="utf-8") as f:
        yaml.dump(prompt_data, f)

    # Create another version
    prompt_data_v2 = prompt_data.copy()
    prompt_data_v2["version"] = "2.0.0"
    prompt_data_v2["system_prompt"] = "Welcome back {{ name }}!"

    with open(d / "test_v2.yaml", "w", encoding="utf-8") as f:
        yaml.dump(prompt_data_v2, f)

    return str(d)


def test_prompt_manager_loading(temp_prompts_dir):
    manager = PromptManager(prompts_dir=temp_prompts_dir)
    prompt = manager.get_prompt("test_prompt", version="1.0.0")
    assert prompt.version == "1.0.0"
    assert prompt.system_prompt == "Hello {{ name }}!"


def test_prompt_manager_latest_version(temp_prompts_dir):
    manager = PromptManager(prompts_dir=temp_prompts_dir)
    prompt = manager.get_prompt("test_prompt")
    assert prompt.version == "2.0.0"
    assert prompt.system_prompt == "Welcome back {{ name }}!"


def test_prompt_manager_rendering(temp_prompts_dir):
    manager = PromptManager(prompts_dir=temp_prompts_dir)
    prompt = manager.get_prompt("test_prompt", version="1.0.0")

    rendered_system = manager.render_prompt(prompt.system_prompt, name="Gemini")
    assert rendered_system == "Hello Gemini!"

    rendered_user = manager.render_prompt(prompt.user_prompt_template, topic="AI")
    assert rendered_user == "Topic: AI"


def test_prompt_manager_invalid_id(temp_prompts_dir):
    manager = PromptManager(prompts_dir=temp_prompts_dir)
    with pytest.raises(ValueError, match="not found"):
        manager.get_prompt("non_existent")


def test_prompt_manager_metadata(tmp_path):
    d = tmp_path / "prompts_meta"
    d.mkdir()

    prompt_data = {
        "id": "meta_prompt",
        "version": "1.0.0",
        "system_prompt": "Hello!",
        "user_prompt_template": "Topic: {{ topic }}",
        "metadata": {
            "performance_target": 0.9,
            "last_optimized_at": "2024-01-01T00:00:00Z",
        },
    }

    with open(d / "meta.yaml", "w", encoding="utf-8") as f:
        yaml.dump(prompt_data, f)

    manager = PromptManager(prompts_dir=str(d))
    prompt = manager.get_prompt("meta_prompt")
    assert prompt.metadata.performance_target == 0.9
    assert prompt.metadata.last_optimized_at == "2024-01-01T00:00:00Z"


def test_prompt_manager_shadow_version(tmp_path):
    d = tmp_path / "prompts_shadow"
    d.mkdir()

    # Version 1 (Shadow Candidate)
    v1 = {
        "id": "shadow_test",
        "version": "1.0.0",
        "system_prompt": "V1",
        "user_prompt_template": "T1",
    }

    # Version 2 (Production with Shadow link)
    v2 = {
        "id": "shadow_test",
        "version": "2.0.0",
        "system_prompt": "V2",
        "user_prompt_template": "T2",
        "shadow_version": "1.0.0",
    }

    with open(d / "v1.yaml", "w", encoding="utf-8") as f:
        yaml.dump(v1, f)
    with open(d / "v2.yaml", "w", encoding="utf-8") as f:
        yaml.dump(v2, f)

    manager = PromptManager(prompts_dir=str(d))
    shadow = manager.get_shadow_prompt("shadow_test")
    assert shadow is not None
    assert shadow.version == "1.0.0"
    assert shadow.system_prompt == "V1"


def test_prompt_manager_thread_safety(temp_prompts_dir):
    import threading

    manager = PromptManager(prompts_dir=temp_prompts_dir)

    def worker():
        for _ in range(100):
            manager.get_prompt("test_prompt")

    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    # If no crash, we consider it "safe enough" for this unit test
