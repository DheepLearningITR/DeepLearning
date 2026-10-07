from dataclasses import dataclass, field


@dataclass
class ToolOutput:
    """What a tool hands back: text for the model, a one-line summary for the timeline."""

    text: str
    summary: str
    ok: bool = True
    extra: dict = field(default_factory=dict)


def function_spec(name: str, description: str, properties: dict, required: list[str] | None = None) -> dict:
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {"type": "object", "properties": properties, "required": required or []},
        },
    }
