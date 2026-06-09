from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StructuredAnswer:
    summary: str
    key_points: list[str]
    caveats: list[str]
    used_chunk_ids: list[str]

    def to_text(self) -> str:
        sections: list[str] = []
        if self.summary:
            sections.append(f"结论：{self.summary}")
        if self.key_points:
            bullet_lines = "\n".join(f"- {item}" for item in self.key_points)
            sections.append(f"关键点：\n{bullet_lines}")
        if self.caveats:
            caveat_lines = "\n".join(f"- {item}" for item in self.caveats)
            sections.append(f"注意：\n{caveat_lines}")
        return "\n\n".join(section for section in sections if section).strip()
