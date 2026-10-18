"""Service-specific schemas, request fields and media shape; shared safety semantics."""

from __future__ import annotations

import json
from typing import Any, Literal

from crewai.tools.tool_failure import ToolFailure
from pydantic import BaseModel, ConfigDict, Field, model_validator

from nano_banana_crewai._base import RetrieveTaskInput, ServiceTool, https_urls


class GenerateInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    model: str = Field(
        min_length=1,
        pattern=r"^nano-banana",
        description="Current public Nano Banana model ID",
    )
    prompt: str = Field(min_length=1)
    action: Literal["generate", "edit"] = "generate"
    image_urls: list[str] | None = None
    count: int = Field(default=1, ge=1, le=4)
    aspect_ratio: Literal["1:1", "3:2", "2:3", "16:9", "9:16", "4:3", "3:4"] | None = (
        None
    )
    resolution: Literal["1K", "2K", "4K"] | None = None

    @model_validator(mode="after")
    def check_edit_input(self):
        if self.action == "edit" and not self.image_urls:
            raise ValueError("edit requires image_urls")
        return self


class _Tool(ServiceTool):
    service = "Nano Banana"
    task_path = "/nano-banana/tasks"

    def _media_urls(self, result: dict[str, Any]) -> list[str]:
        data = result.get("data") or []
        return https_urls(
            [item.get("image_url") for item in data if isinstance(item, dict)]
            if isinstance(data, list)
            else []
        )


class NanoBananaGenerateImageTool(_Tool):
    name: str = "Nano Banana by Ace Data Cloud - Generate Image"
    description: str = "Submit one billable Nano Banana job. Save task_id, then use Retrieve Task on that same ID. Never repeat generation to poll; unknown timeouts require request-history inspection."
    args_schema: type[BaseModel] = GenerateInput
    max_usage_count: int | None = 1

    def _run(self, **parameters: Any) -> str | ToolFailure:
        payload = GenerateInput.model_validate(parameters).model_dump(exclude_none=True)
        payload["async"] = True
        body = self._request("/nano-banana/images", payload)
        result = self._normalize(body, "", retrieved=False)
        return result if isinstance(result, ToolFailure) else json.dumps(result)


class NanoBananaRetrieveTaskTool(_Tool):
    name: str = "Nano Banana by Ace Data Cloud - Retrieve Task"
    description: str = "Read an existing Nano Banana task_id, optionally wait up to 240 seconds. pending is not success. This never creates new media."
    args_schema: type[BaseModel] = RetrieveTaskInput

    def _run(self, task_id: str, wait_seconds: int = 0) -> str | ToolFailure:
        return self._retrieve(task_id, wait_seconds)
