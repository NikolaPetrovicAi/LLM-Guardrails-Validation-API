import os
import yaml
import logging
import threading
from typing import Optional, Dict, List
from jinja2 import Template
from src.models.schemas import PromptDefinition

logger = logging.getLogger(__name__)

class PromptManager:
    """
    Manages externalized LLM prompts with versioning support.
    Supports Shadow Deployment and Metadata tracking.
    """

    def __init__(self, prompts_dir: str = "src/prompts") -> None:
        self.prompts_dir = prompts_dir
        self._prompts: Dict[str, Dict[str, PromptDefinition]] = {}
        self._lock = threading.Lock()
        self.load_all_prompts()

    def load_all_prompts(self) -> None:
        """
        Loads all YAML files from the prompts directory.
        Thread-safe loading.
        """
        if not os.path.exists(self.prompts_dir):
            logger.warning(f"Prompts directory {self.prompts_dir} does not exist.")
            return

        with self._lock:
            for filename in os.listdir(self.prompts_dir):
                if filename.endswith(".yaml") or filename.endswith(".yml"):
                    path = os.path.join(self.prompts_dir, filename)
                    try:
                        with open(path, "r", encoding="utf-8") as f:
                            data = yaml.safe_load(f)
                            prompt_def = PromptDefinition(**data)
                            
                            if prompt_def.id not in self._prompts:
                                self._prompts[prompt_def.id] = {}
                            
                            self._prompts[prompt_def.id][prompt_def.version] = prompt_def
                            shadow_info = f" (Shadow: {prompt_def.shadow_version})" if prompt_def.shadow_version else ""
                            print(f"✅ Loaded prompt: {prompt_def.id} v{prompt_def.version}{shadow_info}")
                            logger.info(f"Loaded prompt: {prompt_def.id} v{prompt_def.version}")
                    except Exception as e:
                        logger.error(f"Failed to load prompt from {path}: {e}")

    def get_prompt(
        self, prompt_id: str, version: Optional[str] = None
    ) -> PromptDefinition:
        """
        Retrieves a specific prompt by ID and version.
        If version is not provided, returns the latest version.
        """
        with self._lock:
            if prompt_id not in self._prompts:
                raise ValueError(f"Prompt with id '{prompt_id}' not found.")

            versions = self._prompts[prompt_id]
            
            if version:
                if version not in versions:
                    raise ValueError(f"Version '{version}' for prompt '{prompt_id}' not found.")
                return versions[version]

            # Get latest version (lexicographical sort of version strings)
            latest_version = sorted(versions.keys())[-1]
            return versions[latest_version]

    def get_shadow_prompt(self, prompt_id: str) -> Optional[PromptDefinition]:
        """
        Retrieves the shadow version of a prompt if configured in the latest version.
        """
        try:
            latest = self.get_prompt(prompt_id)
            if latest.shadow_version:
                return self.get_prompt(prompt_id, latest.shadow_version)
        except Exception as e:
            logger.debug(f"Shadow prompt retrieval failed for {prompt_id}: {e}")
        return None

    def render_prompt(self, template_str: str, **kwargs) -> str:
        """
        Renders a Jinja2 template with provided variables.
        """
        template = Template(template_str)
        return template.render(**kwargs)
