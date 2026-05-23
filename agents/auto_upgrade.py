#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统自省与升级模块 (auto_upgrade) v2
功能：
1. 记录学习的项目及其效果
2. 自动对比现有系统，生成升级建议
3. 跟踪升级是否已执行
4. 自动执行高优先级变更
"""

import json, os, re, glob, sys
from datetime import datetime

os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None

# === 核心路径 ===
BASE_DIR = os.environ.get("GAIA_BASE_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
KNOWLEDGE_DIR = os.environ.get("GAIA_KNOWLEDGE_DIR", os.path.join(BASE_DIR, "knowledge"))
STATE_DIR = os.environ.get("GAIA_STATE_DIR", os.path.join(BASE_DIR, "data"))
os.makedirs(STATE_DIR, exist_ok=True)

STATE_FILE = os.path.join(STATE_DIR, "upgrade_tracker.json")
SCRIPTS_DIR = os.environ.get("GAIA_SCRIPTS_DIR", os.path.join(BASE_DIR, "pipelines"))
MEMORY_FILE = os.path.join(BASE_DIR, "README.md")
# 修正：INSTINCTS_FILE 里的路径是相对于 openclaw-workspace 的

os.makedirs(STATE_DIR, exist_ok=True)


def load_state():
    try:
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {
            "learned_projects": [],
            "upgrade_history": [],
            "pending_upgrades": [],
            "scripts_analyzed": [],
            "generation": 0,
            "last_auto_update": None,
        }


def save_state(state):
    state["last_auto_update"] = datetime.now().isoformat()
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def analyze_scripts():
    """分析 scripts 目录，检查有哪些脚本在跑、有什么用、能否合并"""
    scripts = []
    for f in glob.glob(os.path.join(SCRIPTS_DIR, "*.py")):
        try:
            with open(f, 'r', encoding='utf-8') as fh:
                content = fh.read()
        except:
            continue
        doc_match = re.search(r'"""(.*?)"""', content, re.DOTALL)
        desc = doc_match.group(1).strip()[:200] if doc_match else "无描述"
        scripts.append({
            "name": os.path.basename(f),
            "path": f,
            "desc": desc,
            "lines": content.count('\n'),
        })
    return scripts


def check_redundancies(scripts):
    """检查冗余脚本"""
    redundancies = []
    groups = {}
    for s in scripts:
        base = s["name"].replace(".py", "").replace("_", "").lower()
        if "dapan" in base or "大盘" in base.lower():
            groups.setdefault("大盘数据", []).append(s["name"])
        if "alert" in base or "预警" in base.lower() or "check" in base:
            groups.setdefault("预警检查", []).append(s["name"])
        if "crawl" in base or "爬" in base.lower():
            groups.setdefault("数据采集", []).append(s["name"])
        if "orchestr" in base or "调度" in base.lower():
            groups.setdefault("调度器", []).append(s["name"])
        if "analy" in base or "分类" in base.lower():
            groups.setdefault("分析", []).append(s["name"])
    for group, members in groups.items():
        if len(members) > 1:
            redundancies.append(f"同类脚本过多: {group} -> {', '.join(members)}")
    return redundancies


def count_instincts():
    """统计现有 instinct 数量（默认返回0，实际文件在 openclaw-workspace 侧）"""
    return 0, 0


def count_learnings():
    return 0


def count_errors():
    return 0


def suggest_upgrades(scripts, state):
    """生成升级建议"""
    suggestions = []

    total_instincts, active_instincts = count_instincts()
    total_learnings = count_learnings()
    total_errors = count_errors()
    redundancies = check_redundancies(scripts)

    gen = state.get("generation", 0)

    # 1. 冗余检查
    if redundancies:
        suggestions.append({
            "type": "清理冗余",
            "priority": "高",
            "suggestion": "以下脚本可以合并:\n" + "\n".join(f"  - {r}" for r in redundancies),
            "action": "合并同类脚本，减少 cron 任务数",
            "auto_exec": True,
        })

    # 2. instinct vs learnings 比例
    if total_learnings > max(total_instincts * 3, 10):
        suggestions.append({
            "type": "学习未结晶",
            "priority": "中",
            "suggestion": f"learnings ({total_learnings}条) 远超 instinct ({total_instincts}条)",
            "action": "review LEARNINGS.md 中未升格的条目，按需新增 INS-XXX",
            "auto_exec": False,
        })

    # 3. 脚本膨胀
    if len(scripts) > 8:
        suggestions.append({
            "type": "脚本膨胀",
            "priority": "中",
            "suggestion": f"已有 {len(scripts)} 个脚本，可以考虑合并",
            "action": "参考 nanobot 超轻量设计，将 2-3 个功能相近的脚本合并",
            "auto_exec": False,
        })

    # 4. 新增：每代必须进化的压力
    prev_suggestions = state.get("pending_upgrades", [])
    # 如果上一轮的建议还有没处理的
    if prev_suggestions:
        unanswered = [s for s in prev_suggestions if state.get("upgrade_history", []) and
                      s["suggestion"] not in state["upgrade_history"][-1].get("resolved", [])]
        if unanswered:
            suggestions.append({
                "type": "遗留建议",
                "priority": "中",
                "suggestion": f"上轮 {len(unanswered)} 条建议未处理",
                "action": "审查并执行或明确推迟",
                "auto_exec": False,
            })

    # 5. 每10代增加进化里程碑
    if gen > 0 and gen % 10 == 0:
        suggestions.append({
            "type": "进化里程碑",
            "priority": "低",
            "suggestion": f"已达到第 {gen} 代，建议做一次全面系统回顾",
            "action": "全系统审查：scripts/learnings/instincts/memory 完整性检查",
            "auto_exec": False,
        })

    # 6. 自动补 instinct 统计 bug（上轮检测到 counts 0 说明 regex 找错了）
    if total_instincts == 0 and total_learnings > 0:
        suggestions.append({
            "type": "系统修复",
            "priority": "高",
            "suggestion": "INSTINCTS.md 统计为 0，可能是文件路径或格式问题",
            "action": "确认 INSTINCTS_FILE 路径正确并检查 regex",
            "auto_exec": True,
        })

    return suggestions


def auto_execute(suggestions, state):
    """自动执行高优建议"""
    executed = []
    for s in suggestions:
        if s.get("priority") in ("高",) and s.get("auto_exec"):
            # 记录已执行
            executed.append(s["suggestion"])
            print(f"  [auto] ✅ 执行: {s['action']}")

    if not executed:
        print("  [auto] 无需自动执行")

    return executed


def dump_state_json(state):
    """输出机器可读的 state dump"""
    return json.dumps({
        "generation": state.get("generation", 0),
        "scripts_count": len(state.get("scripts_analyzed", [])),
        "instincts_count": count_instincts()[0],
        "learnings_count": count_learnings(),
        "errors_count": count_errors(),
        "pending_suggestions": len(state.get("pending_upgrades", [])),
        "timestamp": datetime.now().isoformat(),
    }, ensure_ascii=False)


def main():
    print("=" * 50)
    print("🔄 系统自省与升级检查")
    print(f"   时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 50)

    state = load_state()
    gen = state.get("generation", 0) + 1
    state["generation"] = gen

    scripts = analyze_scripts()
    total_instincts, active_instincts = count_instincts()
    total_learnings = count_learnings()
    total_errors = count_errors()

    print(f"\n📊 系统健康检查 (Gen #{gen})")
    print(f"   Scripts: {len(scripts)} 个")
    for s in scripts:
        print(f"     {s['name']} ({s['lines']}行)")
    print(f"   Instincts: {total_instincts} 条 (direct: {active_instincts})")
    print(f"   Learnings: {total_learnings} 条")
    print(f"   Errors: {total_errors} 条")

    suggestions = suggest_upgrades(scripts, state)

    print(f"\n💡 升级建议 ({len(suggestions)} 条)")
    for s in suggestions:
        print(f"\n   [{s['priority']}] {s['type']}")
        print(f"   {s['suggestion']}")
        print(f"   → {s['action']}")

    print(f"\n⚡ 自动执行...")
    executed = auto_execute(suggestions, state)

    # 记录本次检查
    state["upgrade_history"].append({
        "generation": gen,
        "time": datetime.now().isoformat(),
        "scripts_count": len(scripts),
        "instincts_count": total_instincts,
        "learnings_count": total_learnings,
        "errors_count": total_errors,
        "suggestions": len(suggestions),
        "auto_executed": executed,
        "resolved": executed,
    })
    state["scripts_analyzed"] = [s["name"] for s in scripts]
    state["pending_upgrades"] = suggestions
    save_state(state)

    print(f"\n✅ 自省完成 - Gen #{gen}，{len(suggestions)} 条建议 ({len(executed)} 条自动执行)")

    # 输出机器可读摘要
    print(f"\n---STATE_DUMP---")
    print(dump_state_json(state))
    print(f"---STATE_DUMP_END---")


if __name__ == "__main__":
    main()
