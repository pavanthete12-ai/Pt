from pydantic import BaseModel, Field

class PluginManifest(BaseModel):
    id: str
    name: str
    version: str
    entrypoint: str
    permissions: list[str] = Field(default_factory=list)
