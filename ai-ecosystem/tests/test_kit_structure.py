"""キットの構造検査（Windows でなくても検証できる部分）。"""
import json
import re
import unittest
from pathlib import Path

KIT = Path(__file__).resolve().parents[1]
HOME = KIT / "claude-home"


def frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n"), f"{path}: frontmatter は1行目から"
    body = text.split("---", 2)[1]
    out = {}
    for line in body.strip().splitlines():
        if ":" in line and not line.startswith(" "):
            k, v = line.split(":", 1)
            out[k.strip()] = v.strip()
    return out


class KitTest(unittest.TestCase):
    def test_skills(self):
        names = set()
        for d in sorted((HOME / "skills").iterdir()):
            fm = frontmatter(d / "SKILL.md")
            self.assertEqual(fm.get("name"), d.name)
            self.assertTrue(fm.get("description"))
            self.assertLessEqual(len(fm["description"]), 1536)
            self.assertLess(len((d / "SKILL.md").read_text(encoding="utf-8").splitlines()), 500)
            names.add(d.name)
        self.assertEqual(names, {"research", "stock-a", "stock-b", "business-review", "project-build", "content-production", "remember"})

    def test_agents(self):
        for f in sorted((HOME / "agents").glob("*.md")):
            fm = frontmatter(f)
            self.assertEqual(fm.get("name"), f.stem)
            self.assertTrue(fm.get("description"))
            self.assertNotIn(":", fm["name"])
            tools = {t.strip() for t in fm.get("tools", "").split(",")}
            self.assertNotIn("Agent", tools, "サブエージェントから更に委任させない")
            if f.stem in ("quality-reviewer", "technical-qa", "research-analyst"):
                self.assertFalse(tools & {"Edit", "Write"}, f"{f.stem} は編集権限を持たない")

    def test_settings_template_renders_to_valid_json(self):
        text = (HOME / "settings.template.json").read_text(encoding="utf-8")
        hooks = r"C:\Users\me\.claude\hooks\ai-ecosystem".replace("\\", "\\\\")
        vault = r"C:\Users\me\Documents\Vault".replace("\\", "\\\\")
        s = json.loads(text.replace("{{HOOKS_DIR}}", hooks).replace("{{VAULT_PATH}}", vault))
        p = s["permissions"]
        self.assertEqual(p["defaultMode"], "default")
        self.assertEqual(p["disableBypassPermissionsMode"], "disable")
        self.assertIn("Read(**/.env)", p["deny"])
        for ev in ("SessionStart", "PreToolUse", "PostToolUse", "Stop"):
            for group in s["hooks"][ev]:
                for h in group["hooks"]:
                    script = Path(h["args"][-1].replace("\\", "/")).name
                    self.assertTrue((HOME / "hooks" / script).exists(), script)
                    self.assertLessEqual(h["timeout"], 30)

    def test_claude_md_short_and_placeholders(self):
        t = (HOME / "CLAUDE.md").read_text(encoding="utf-8")
        self.assertLess(len(t.splitlines()), 200)
        self.assertEqual(set(re.findall(r"\{\{(\w+)\}\}", t)), {"AI_HUB"})

    def test_ps1_have_bom(self):
        for p in KIT.rglob("*.ps1"):
            self.assertTrue(p.read_bytes().startswith(b"\xef\xbb\xbf"), f"{p} は UTF-8 BOM 付きにする（PowerShell 5.1 対策）")

    def test_obsidian_template_links_exist(self):
        tpl = KIT / "obsidian-template" / "AI_Hub"
        notes = {p.stem for p in tpl.rglob("*.md")}
        for p in tpl.rglob("*.md"):
            for link in re.findall(r"\[\[([^\]|]+)", p.read_text(encoding="utf-8")):
                self.assertIn(Path(link).stem, notes, f"{p.name} のリンク先 {link} がない")


if __name__ == "__main__":
    unittest.main()
