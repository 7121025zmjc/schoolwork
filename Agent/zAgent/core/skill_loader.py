# -*- coding: utf-8 -*-
"""Skill 发现与加载：扫描 .agents/skills/ 目录，解析 SKILL.md。

每个 Skill 是一个子目录，至少包含一个 SKILL.md 文件，
文件开头用 YAML Frontmatter 声明 name 和 description。
初始化时只加载 name/description 注入 system prompt，
完整正文通过 loadSkill 工具按需加载。"""
import os
import re

SKILLS_DIR = ".agents" + os.sep + "skills"


def _parse_frontmatter(text):
    """解析 SKILL.md 开头的 YAML Frontmatter，返回 (meta, body)。"""
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.DOTALL)
    if not m:
        return {}, text
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta, m.group(2)


def discover_skills(base_dir=None):
    """扫描 skills 目录，返回 [{name, description, path, skill_md}]。

    初始化阶段只读取 name 和 description，不读正文。
    """
    if base_dir is None:
        base_dir = os.getcwd()
    skills_root = os.path.join(base_dir, SKILLS_DIR)
    skills = []
    if not os.path.isdir(skills_root):
        return skills
    for entry in os.listdir(skills_root):
        skill_dir = os.path.join(skills_root, entry)
        skill_md = os.path.join(skill_dir, "SKILL.md")
        if not os.path.isfile(skill_md):
            continue
        try:
            with open(skill_md, "r", encoding="utf-8") as f:
                text = f.read()
            meta, _ = _parse_frontmatter(text)
            name = meta.get("name", entry)
            desc = meta.get("description", "")
            skills.append({
                "name": name,
                "description": desc,
                "path": skill_dir,
                "skill_md": skill_md,
            })
        except Exception:
            continue
    return skills


def load_skill_body(name, base_dir=None):
    """按名称加载某个 Skill 的 SKILL.md 全文。"""
    if base_dir is None:
        base_dir = os.getcwd()
    skills_root = os.path.join(base_dir, SKILLS_DIR)
    skill_dir = os.path.join(skills_root, name)
    skill_md = os.path.join(skill_dir, "SKILL.md")
    if not os.path.isfile(skill_md):
        return "未找到 Skill: %s" % name
    with open(skill_md, "r", encoding="utf-8") as f:
        return f.read()


def load_skill_file(name, filename, base_dir=None):
    """在指定 Skill 目录内加载附加文件，不跳出 Skill 目录。"""
    if base_dir is None:
        base_dir = os.getcwd()
    skills_root = os.path.join(base_dir, SKILLS_DIR)
    skill_dir = os.path.join(skills_root, name)
    if not os.path.isdir(skill_dir):
        return "未找到 Skill: %s" % name
    # 防止路径逃逸
    target = os.path.normpath(os.path.join(skill_dir, filename))
    if not target.startswith(os.path.normpath(skill_dir)):
        return "错误：不允许访问 Skill 目录之外的文件"
    if os.path.isfile(target):
        with open(target, "r", encoding="utf-8") as f:
            return f.read()
    # 递归搜索文件名
    candidates = []
    for root, _, files in os.walk(skill_dir):
        for fn in files:
            if fn == os.path.basename(filename):
                candidates.append(os.path.join(root, fn))
    if len(candidates) == 1:
        with open(candidates[0], "r", encoding="utf-8") as f:
            return f.read()
    if len(candidates) > 1:
        return "找到多个同名文件，请指定路径：\n" + "\n".join(candidates)
    return "未找到文件: %s" % filename


def build_skills_prompt(skills):
    """把 Skill 列表整理成 system prompt 片段。"""
    if not skills:
        return ""
    lines = ["You have access to the following skills:"]
    for s in skills:
        lines.append("- %s: %s" % (s["name"], s["description"]))
    lines.append("Use the loadSkill tool to load a skill's full instructions when needed.")
    return "\n".join(lines)
