from typing import List, Optional

from pydantic import BaseModel, Field, model_validator

from letta.constants import LLM_MAX_TOKENS
from letta.llm_api.azure_openai import (
    get_azure_chat_completions_endpoint,
    get_azure_embeddings_endpoint,
)
from letta.llm_api.azure_openai_constants import AZURE_MODEL_TO_CONTEXT_LENGTH
from letta.schemas.embedding_config import EmbeddingConfig
from letta.schemas.llm_config import LLMConfig


class Provider(BaseModel):
    base_url: str

    def list_llm_models(self):
        return []

    def list_embedding_models(self):
        return []

    def get_model_context_window(self, model_name: str):
        pass


class OpenAIProvider(Provider):
    name: str = "openai"
    api_key: str = Field(..., description="API key for the OpenAI API.")
    base_url: str = "https://api.openai.com/v1"

    def list_llm_models(self) -> List[LLMConfig]:
        from letta.llm_api.openai import openai_get_model_list

        response = openai_get_model_list(self.base_url, api_key=self.api_key)
        model_options = [obj["id"] for obj in response["data"]]

        configs = []
        for model_name in model_options:
            context_window_size = self.get_model_context_window_size(model_name)

            if not context_window_size:
                continue
            configs.append(
                LLMConfig(model=model_name, model_endpoint_type="openai", model_endpoint=self.base_url, context_window=context_window_size)
            )
        return configs

    def list_embedding_models(self) -> List[EmbeddingConfig]:

        # TODO: actually automatically list models
        return [
            EmbeddingConfig(
                embedding_model="text-embedding-ada-002",
                embedding_endpoint_type="openai",
                embedding_endpoint="https://api.openai.com/v1",
                embedding_dim=1536,
                embedding_chunk_size=300,
            )
        ]

    def get_model_context_window_size(self, model_name: str):
        if model_name in LLM_MAX_TOKENS:
            return LLM_MAX_TOKENS[model_name]
        else:
            return None


class AnthropicProvider(Provider):
    name: str = "anthropic"
    api_key: str = Field(..., description="API key for the Anthropic API.")
    base_url: str = "https://api.anthropic.com/v1"

    def list_llm_models(self) -> List[LLMConfig]:
        from letta.llm_api.anthropic import anthropic_get_model_list

        models = anthropic_get_model_list(self.base_url, api_key=self.api_key)

        configs = []
        for model in models:
            configs.append(
                LLMConfig(
                    model=model["name"],
                    model_endpoint_type="anthropic",
                    model_endpoint=self.base_url,
                    context_window=model["context_window"],
                )
            )
        return configs

    def list_embedding_models(self) -> List[EmbeddingConfig]:
        return []


class OllamaProvider(OpenAIProvider):
    name: str = "ollama"
    base_url: str = Field(..., description="Base URL for the Ollama API.")
    api_key: Optional[str] = Field(None, description="API key for the Ollama API (default: `None`).")

    def list_llm_models(self) -> List[LLMConfig]:
        # https://github.com/ollama/ollama/blob/main/docs/api.md#list-local-models
        import requests

        response = requests.get(f"{self.base_url}/api/tags")
        if response.status_code != 200:
            raise Exception(f"Failed to list Ollama models: {response.text}")
        response_json = response.json()

        configs = []
        for model in response_json["models"]:
            context_window = self.get_model_context_window(model["name"])
            configs.append(
                LLMConfig(
                    model=model["name"],
                    model_endpoint_type="ollama",
                    model_endpoint=self.base_url,
                    context_window=context_window,
                )
            )
        return configs

    def get_model_context_window(self, model_name: str):

        import requests

        response = requests.post(f"{self.base_url}/api/show", json={"name": model_name, "verbose": True})
        response_json = response.json()

        # thank you vLLM: https://github.com/vllm-project/vllm/blob/main/vllm/config.py#L1675
        possible_keys = [
            # OPT
            "max_position_embeddings",
            # GPT-2
            "n_positions",
            # MPT
            "max_seq_len",
            # ChatGLM2
            "seq_length",
            # Command-R
            "model_max_length",
            # Others
            "max_sequence_length",
            "max_seq_length",
            "seq_len",
        ]

        # max_position_embeddings
        # parse model cards: nous, dolphon, llama
        for key, value in response_json["model_info"].items():
            if "context_window" in key:
                return value
        return None

    def list_embedding_models(self) -> List[EmbeddingConfig]:
        # TODO: filter embedding models
        return []


class GroqProvider(OpenAIProvider):
    name: str = "groq"
    base_url: str = "https://api.groq.com/openai/v1"
    api_key: str = Field(..., description="API key for the Groq API.")

    def list_llm_models(self) -> List[LLMConfig]:
        from letta.llm_api.openai import openai_get_model_list

        response = openai_get_model_list(self.base_url, api_key=self.api_key)
        configs = []
        for model in response["data"]:
            if not "context_window" in model:
                continue
            configs.append(
                LLMConfig(
                    model=model["id"], model_endpoint_type="openai", model_endpoint=self.base_url, context_window=model["context_window"]
                )
            )
        return configs

    def list_embedding_models(self) -> List[EmbeddingConfig]:
        return []

    def get_model_context_window_size(self, model_name: str):
        raise NotImplementedError


class GoogleAIProvider(Provider):
    # gemini
    api_key: str = Field(..., description="API key for the Google AI API.")
    service_endpoint: str = "generativelanguage"  # TODO: remove once old functions are refactored to just use base_url
    base_url: str = "https://generativelanguage.googleapis.com"

    def list_llm_models(self):
        from letta.llm_api.google_ai import google_ai_get_model_list

        # TODO: use base_url instead
        model_options = google_ai_get_model_list(service_endpoint=self.service_endpoint, api_key=self.api_key)
        # filter by 'generateContent' models
        model_options = [mo for mo in model_options if "generateContent" in mo["supportedGenerationMethods"]]
        model_options = [str(m["name"]) for m in model_options]

        # filter by model names
        model_options = [mo[len("models/") :] if mo.startswith("models/") else mo for mo in model_options]

        # TODO remove manual filtering for gemini-pro
        model_options = [mo for mo in model_options if str(mo).startswith("gemini") and "-pro" in str(mo)]

        configs = []
        for model in model_options:
            configs.append(
                LLMConfig(
                    model=model,
                    model_endpoint_type="google_ai",
                    model_endpoint=self.base_url,
                    context_window=self.get_model_context_window(model),
                )
            )
        return configs

    def list_embedding_models(self):
        from letta.llm_api.google_ai import google_ai_get_model_list

        # TODO: use base_url instead
        model_options = google_ai_get_model_list(service_endpoint=self.service_endpoint, api_key=self.api_key)
        # filter by 'generateContent' models
        model_options = [mo for mo in model_options if "embedContent" in mo["supportedGenerationMethods"]]
        model_options = [str(m["name"]) for m in model_options]
        model_options = [mo[len("models/") :] if mo.startswith("models/") else mo for mo in model_options]

        configs = []
        for model in model_options:
            configs.append(
                EmbeddingConfig(
                    embedding_model=model,
                    embedding_endpoint_type="google_ai",
                    embedding_endpoint=self.base_url,
                    embedding_dim=768,
                    embedding_chunk_size=300,  # NOTE: max is 2048
                )
            )
        return configs

    def get_model_context_window(self, model_name: str):
        from letta.llm_api.google_ai import google_ai_get_model_context_window

        # TODO: use base_url instead
        return google_ai_get_model_context_window(self.service_endpoint, self.api_key, model_name)


class AzureProvider(Provider):
    name: str = "azure"
    latest_api_version: str = "2024-09-01-preview"  # https://learn.microsoft.com/en-us/azure/ai-services/openai/api-version-deprecation
    base_url: str = Field(
        ..., description="Base URL for the Azure API endpoint. This should be specific to your org, e.g. `https://letta.openai.azure.com`."
    )
    api_key: str = Field(..., description="API key for the Azure API.")
    api_version: str = Field(latest_api_version, description="API version for the Azure API")

    @model_validator(mode="before")
    def set_default_api_version(cls, values):
        """
        This ensures that api_version is always set to the default if None is passed in.
        """
        if values.get("api_version") is None:
            values["api_version"] = cls.model_fields["latest_api_version"].default
        return values

    def list_llm_models(self) -> List[LLMConfig]:
        from letta.llm_api.azure_openai import (
            azure_openai_get_chat_completion_model_list,
        )

        model_options = azure_openai_get_chat_completion_model_list(self.base_url, api_key=self.api_key, api_version=self.api_version)
        configs = []
        for model_option in model_options:
            model_name = model_option["id"]
            context_window_size = self.get_model_context_window(model_name)
            model_endpoint = get_azure_chat_completions_endpoint(self.base_url, model_name, self.api_version)
            configs.append(
                LLMConfig(model=model_name, model_endpoint_type="azure", model_endpoint=model_endpoint, context_window=context_window_size)
            )
        return configs

    def list_embedding_models(self) -> List[EmbeddingConfig]:
        from letta.llm_api.azure_openai import azure_openai_get_embeddings_model_list

        model_options = azure_openai_get_embeddings_model_list(
            self.base_url, api_key=self.api_key, api_version=self.api_version, require_embedding_in_name=True
        )
        configs = []
        for model_option in model_options:
            model_name = model_option["id"]
            model_endpoint = get_azure_embeddings_endpoint(self.base_url, model_name, self.api_version)
            configs.append(
                EmbeddingConfig(
                    embedding_model=model_name,
                    embedding_endpoint_type="azure",
                    embedding_endpoint=model_endpoint,
                    embedding_dim=768,
                    embedding_chunk_size=300,  # NOTE: max is 2048
                )
            )
        return configs

    def get_model_context_window(self, model_name: str):
        """
        This is hardcoded for now, since there is no API endpoints to retrieve metadata for a model.
        """
        return AZURE_MODEL_TO_CONTEXT_LENGTH.get(model_name, 4096)


class VLLMProvider(OpenAIProvider):
    # NOTE: vLLM only serves one model at a time (so could configure that through env variables)
    pass


class CohereProvider(OpenAIProvider):
    pass
