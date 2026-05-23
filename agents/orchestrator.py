#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多Agent进化引擎 (orchestrator v3)
===================================
功能：
1. 品类数据分析 + 预警更新 + 飞书推送（原功能）
2. 系统自省：检查自身脚本健康状况（调用 auto_upgrade.py 子模块）
3. 学习结晶器：从 LEARNINGS.md 自动识别可结晶的 instinct 候选
4. 进化日志：每次运行记录到 EVOLUTION.md
5. 每15分钟由 cron 触发
"""

import json, os, glob, time, hashlib, sys, re
from datetime import datetime

os.environ['PYTHONIOENCODING'] = 'utf-8'
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# ===== 核心路径 =====
# ===== 核心路径（可通过环境变量覆盖）=====
BASE_DIR = os.environ.get("GAIA_BASE_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
KNOWLEDGE_DIR = os.environ.get("GAIA_KNOWLEDGE_DIR", os.path.join(BASE_DIR, "knowledge"))
STATE_DIR = os.environ.get("GAIA_STATE_DIR", os.path.join(BASE_DIR, "data"))
os.makedirs(STATE_DIR, exist_ok=True)

STATE_FILE = os.path.join(STATE_DIR, "orchestrator_state.json")
EVOLUTION_FILE = os.path.join(STATE_DIR, "EVOLUTION.md")
OUTPUT_DIR = os.path.join(KNOWLEDGE_DIR, "reports")
ALERTS_FILE = os.path.join(BASE_DIR, "config", "alerts.json")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(os.path.dirname(ALERTS_FILE), exist_ok=True)

# ============================================================
# 工具函数
# ============================================================

from shared.feishu import push_feishu, get_feishu_token

def load_state():
    try:
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"processed_files": {}, "last_check": None, "alerts_updated": False,
                "self_heal_count": 0, "gen_count": 0}

def save_state(state):
    state["last_check"] = datetime.now().isoformat()
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def file_hash(path):
    with open(path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

def is_new_file(path, state):
    h = file_hash(path)
    key = os.path.basename(path)
    prev = state["processed_files"].get(key)
    if prev is None:
        return True
    if prev["hash"] != h:
        return True
    last_processed = prev.get("processed_at")
    if last_processed:
        try:
            dt = datetime.fromisoformat(last_processed)
            if (datetime.now() - dt).total_seconds() < 300:
                return False
        except:
            pass
    return prev["hash"] != h

def mark_processed(path, state, status="ok"):
    key = os.path.basename(path)
    state["processed_files"][key] = {
        "hash": file_hash(path),
        "processed_at": datetime.now().isoformat(),
        "status": status
    }

# ============================================================
# 模块 1：品类分析（原orchestrator功能）
# ============================================================

class CategoryAnalyzer:
    @staticmethod
    def update_alerts(category_data):
        alerts = {}
        try:
            with open(ALERTS_FILE, 'r', encoding='utf-8') as f:
                alerts = json.load(f)
        except:
            pass
        for cat in category_data:
            name = cat.get("name", cat.get("type", "?"))
            if name in ["冲锋枪", "霰弹枪"]:
                continue
            items = cat.get("items", [])
            if not items:
                continue
            key = f"品类:{name}"
            prices = [i.get("price", 0) for i in items if i.get("price")]
            alerts[key] = {
                "enabled": True,
                "description": f"{name}品类行情监控",
                "items": [{"name": i.get("name", ""), "price": i.get("price", 0),
                           "market": i.get("marketHashName", "")} for i in items[:5]],
                "avg_price": sum(prices) / max(len(prices), 1),
                "updated_at": datetime.now().isoformat()
            }
        with open(ALERTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(alerts, f, ensure_ascii=False, indent=2)
        return list(alerts.keys())

    @staticmethod
    def generate_report(category_files):
        now = datetime.now()
        all_cats = []
        for fpath in category_files:
            with open(fpath, 'r', encoding='utf-8') as f:
                d = json.load(f)
            all_cats.append(d)
        report_path = os.path.join(OUTPUT_DIR, f"{now.strftime('%Y-%m-%d')}-品类报告.md")
        lines = [
            f"# 品类分析报告 | {now.strftime('%Y-%m-%d')}",
            f"> 生成时间: {now.strftime('%Y-%m-%d %H:%M')}",
            "",
            "---",
            "## 品类概览",
            "",
            "| 品类 | 饰品数 | 均价 | 最高 | 最低 |",
            "|------|--------|------|------|------|",
        ]
        for d in all_cats:
            items = d.get("items", [])
            prices = [i.get("price", 0) for i in items if i.get("price")]
            if not prices:
                continue
            avg = f"{sum(prices)/len(prices):.2f}"
            hi = f"{max(prices):.2f}"
            lo = f"{min(prices):.2f}"
            lines.append(f"| {d.get('name', d.get('type', '?'))} | {len(items)} | {avg} | {hi} | {lo} |")
        lines.extend(["", "## 千元以下推荐", ""])
        for d in all_cats:
            items = d.get("items", [])
            cheap = [i for i in items if 0 < i.get("price", 0) < 1000]
            if cheap:
                lines.append(f"### {d.get('name', d.get('type', '?'))}")
                for item in cheap[:5]:
                    p = item.get("price", 0)
                    lines.append(f"- {item['name']} — ¥{p:.2f}")
                lines.append("")
        report = "\n".join(lines)
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        return report, report_path

# ============================================================
# 模块 2：系统自省（调用 auto_upgrade 逻辑）
# ============================================================

class SelfHealer:
    """自我修复引擎：检查关键文件完整性和配置一致性"""
    
    @staticmethod
    def check_critical_files():
        """检查关键文件是否存在、可读"""
        issues = []
        for name, path in CRITICAL_FILES.items():
            if not os.path.exists(path):
                issues.append(f"缺失: {name} ({path})")
                continue
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    f.read(10)
            except:
                issues.append(f"不可读: {name} ({path})")
        return issues
    
    @staticmethod
    def check_encoding_consistency():
        """检查所有 .py 文件是否都设了 PYTHONIOENCODING"""
        issues = []
        for script in glob.glob(os.path.join(KNOWLEDGE_DIR, "scripts", "*.py")):
            with open(script, 'r', encoding='utf-8') as f:
                content = f.read()
            if "PYTHONIOENCODING" not in content and "utf" not in content:
                issues.append(f"编码保护缺失: {os.path.basename(script)}")
        return issues
    
    @staticmethod
    def check_instinct_confidence_drift():
        """发现 confidence 在 0.5-0.7 但从未被引用的 instinct"""
        try:
            with open(os.path.join(BASE_DIR, ".learnings", "INSTINCTS.md"), 'r', encoding='utf-8') as f:
                content = f.read()
            # 找 confidence 0.6-0.7 的 instinct
            low_conf = re.findall(r'## (INS-\d+):.*?\*\*Confidence\*\*: (0\.[6-7]\d)', content)
            return low_conf if low_conf else []
        except:
            return []
    
    @staticmethod
    def fix_minor_issues(issues):
        """自动修复小问题"""
        fixes = []
        for issue in issues:
            if "编码保护缺失" in issue:
                fixes.append(f"⚠️ {issue} (需手动添加 PYTHONIOENCODING)")
        return fixes

# ============================================================
# 模块 3a：学习结晶器 (Learnings -> Instincts gateway)
# ============================================================

class LearningCrystallizer:
    """自动从 LEARNINGS.md 中识别可以升格为 instinct 的候选"""
    
    @staticmethod
    def scan_for_candidates():
        """扫描 LEARNINGS.md 中 status=resolved 且未升格的条目"""
        candidates = []
        try:
            with open(os.path.join(BASE_DIR, ".learnings", "LEARNINGS.md"), 'r', encoding='utf-8') as f:
                content = f.read()
            entries = content.split("## [")
            for entry in entries[1:]:  # skip header
                status_match = re.search(r'\*\*Status\*\*: (\w+)', entry)
                area_match = re.search(r'\*\*Area\*\*: (\w+)', entry)
                summary_match = re.search(r'### Summary\n(.+)', entry)
                id_match = re.search(r'LRN-(\d+-\d+)', entry)
                resolved = status_match and status_match.group(1) == "resolved"
                if not resolved:
                    continue
                if summary_match:
                    candidates.append({
                        "id": f"LRN-{id_match.group(1)}" if id_match else "?",
                        "summary": summary_match.group(1).strip()[:100],
                        "area": area_match.group(1) if area_match else "?",
                        "action_hint": "→ 可以结晶为 INS-015+"
                    })
        except:
            pass
        return candidates[:5]  # 最多推荐5条

# ============================================================
# 模块 4：进化日志写入
# ============================================================

# ============================================================
# 模块 3b: 自动修复器 (AutoFixer)
# ============================================================

class AutoFixer:
    """自动修复模块：检测并执行实际清理"""
    
    @staticmethod
    def clean_temp_files():
        """清理临时文件"""
        cleaned = 0
        for f in glob.glob(os.path.join(KNOWLEDGE_DIR, "scripts", "_*.py")):
            try:
                os.remove(f)
                cleaned += 1
                print(f"  🗑️ 删除临时脚本: {os.path.basename(f)}")
            except:
                pass
        for f in glob.glob(os.path.join(OUTPUT_DIR, "*.md")):
            try:
                age = (datetime.now().timestamp() - os.path.getmtime(f)) / 86400
                if age > 7:
                    os.remove(f)
                    cleaned += 1
            except:
                pass
        return cleaned
    
    @staticmethod
    def check_scripts_health():
        """检查脚本冗余是否已解决"""
        scripts_dir = os.path.join(KNOWLEDGE_DIR, "scripts")
        scripts = [os.path.basename(f) for f in glob.glob(os.path.join(scripts_dir, "*.py"))]
        count = len(scripts)
        crawl_count = sum(1 for s in scripts if 'crawl' in s.lower() or 'push' in s.lower())
        return count, crawl_count, scripts
    
    @staticmethod
    def log_health(scripts, evo):
        count, crawl_count, names = AutoFixer.check_scripts_health()
        # 判断脚本精简度
        if count > 8:
            evo.add("脚本精简", f"{count}个 (偏多, crawl/push残余{crawl_count}个)", "WARN")
        elif count >= 5:
            evo.add("脚本精简", f"{count}个 (健康)", "INFO")
        else:
            evo.add("脚本精简", f"{count}个 (偏少)", "INFO")


class EvolutionLogger:
    def __init__(self):
        self.entries = []
    
    def add(self, section, message, level="INFO"):
        self.entries.append({
            "time": datetime.now().strftime("%H:%M"),
            "section": section,
            "message": message,
            "level": level,
            "ts": datetime.now().isoformat()
        })
    
    def summaries(self):
        infos = [e for e in self.entries if e["level"] == "INFO"]
        warns = [e for e in self.entries if e["level"] == "WARN"]
        errs = [e for e in self.entries if e["level"] == "ERROR"]
        parts = []
        if infos:
            parts.append(f"  ✅ {len(infos)} 条正常处理")
        if warns:
            parts.append(f"  ⚠️ {len(warns)} 条警告")
        if errs:
            parts.append(f"  ❌ {len(errs)} 条错误")
        return "\n".join(parts) if parts else "  一切正常"
    
    def write_to_file(self):
        today = datetime.now().strftime("%Y-%m-%d")
        today_short = datetime.now().strftime("%m-%d")
        evo_file = os.path.join(STATE_DIR, "EVOLUTION.md")
        
        try:
            with open(evo_file, 'r', encoding='utf-8') as f:
                existing = f.read()
        except:
            existing = "# 🧬 进化日志\n\n系统自动进化记录。\n"
        
        # 只记录 WARN / ERROR / 关键变化，不刷 INFO
        significant = [e for e in self.entries if e["level"] in ("WARN", "ERROR") or 
                       (e["section"] in ("品类分析", "自愈", "脚本精简") and "清理" in e["message"])]
        
        if not significant:
            return  # 静默，不记录重复的 INFO
        
        sig_key = " | ".join(f"{e['section']}:{e['message'][:30]}" for e in significant)
        # 检查最近是否记录过完全一样的日志（去重）
        if sig_key in existing[-5000:]:
            return  # 刚记录过，不再重复
        
        date_header = f"\n| {today_short} |"
        run_entry = f"{datetime.now().strftime('%H:%M')}: "
        run_entry += "; ".join(f"{'⚠️' if e['level']=='WARN' else '❌'} {e['section']}: {e['message'][:60]}" for e in significant)
        
        if date_header in existing:
            # 追加到当日表格
            existing = existing.replace(date_header, date_header + "\n" + run_entry)
        else:
            # 没有当天表头，追加结构
            existing += f"{date_header} {run_entry}\n"
        
        with open(evo_file, 'w', encoding='utf-8') as f:
            f.write(existing)


# ============================================================
# Main 进化循环
# ============================================================

def main():
    now = datetime.now()
    evo = EvolutionLogger()
    state = load_state()
    
    gen = state.get("gen_count", 0) + 1
    state["gen_count"] = gen
    
    print(f"🧬 进化引擎 Gen #{gen} | {now.strftime('%Y-%m-%d %H:%M')}")
    print("=" * 50)
    
    # === 模块A: 品类数据分析 ===
    cat_files = glob.glob(os.path.join(STEAMDT_DIR, "*_排行榜.json"))
    new_cat_files = [f for f in cat_files if is_new_file(f, state)]
    
    if new_cat_files:
        print(f"\n📦 新品类数据: {len(new_cat_files)} 个文件")
        for f in new_cat_files:
            print(f"  {os.path.basename(f)}")
            mark_processed(f, state)
        
        # 更新预警
        all_data = []
        for f in new_cat_files:
            with open(f, 'r', encoding='utf-8') as fd:
                d = json.load(fd)
            all_data.append({
                "name": os.path.basename(f).replace("_排行榜.json", ""),
                "items": d.get("items", []),
            })
        cat_analyzer = CategoryAnalyzer()
        cat_analyzer.update_alerts(all_data)
        report, report_path = cat_analyzer.generate_report(new_cat_files)
        
        # 推飞书通知
        msg_lines = [f"📊 品类数据更新 | {now.strftime('%Y-%m-%d %H:%M')}"]
        for d in all_data:
            prices = [i.get("price", 0) for i in d.get("items", []) if i.get("price")]
            avg = sum(prices)/len(prices) if prices else 0
            msg_lines.append(f"📦 {d['name']}: {len(prices)}件, 均价¥{avg:.0f}")
        msg_lines.append(f"\n📄 报告已生成")
        push_feishu("\n".join(msg_lines))
        
        evo.add("品类分析", f"处理 {len(new_cat_files)} 个品类文件, 推飞书通知")
        print(f"  ✅ 品类分析完成")
    else:
        print(f"\n📦 无新品类数据")
    
    # === 模块B: 系统自省 ===
    healer = SelfHealer()
    file_issues = healer.check_critical_files()
    enc_issues = healer.check_encoding_consistency()
    drift_issues = healer.check_instinct_confidence_drift()
    
    all_issues = file_issues + enc_issues
    if drift_issues:
        for ins, conf in drift_issues:
            print(f"  ⚠️ 低活跃 instinct: {ins} (conf={conf})")
    
    if all_issues:
        fixes = healer.fix_minor_issues(all_issues)
        for issue in all_issues:
            evo.add("自检", issue, "WARN")
            print(f"  ⚠️ {issue}")
        for fix in fixes:
            evo.add("自愈", fix, "INFO")
    else:
        evo.add("自检", "所有关键文件正常", "INFO")
        print(f"  ✅ 系统自检健康")
    
    # === 模块C: 自动修复 ===
    fixer = AutoFixer()
    cleaned = fixer.clean_temp_files()
    if cleaned:
        evo.add("自愈", f"清理了 {cleaned} 个临时/过期文件", "INFO")
        print(f"  🗑️ 清理 {cleaned} 个文件")
    fixer.log_health(None, evo)
    
    # === 模块D: 学习结晶 ===
    candidates = LearningCrystallizer.scan_for_candidates()
    # 跟踪已报告的候选，只在新出现时记录
    prev_candidates = set(state.get("reported_candidates", []))
    new_candidates = [c for c in candidates if c["id"] not in prev_candidates]
    if new_candidates:
        for c in new_candidates:
            evo.add("结晶候选", f"{c['id']}: {c['summary']} {c['action_hint']}", "WARN")
        print(f"  ⚠️ 新发现 {len(new_candidates)} 条可结晶学习")
    state["reported_candidates"] = [c["id"] for c in candidates]
    if not candidates:
        print(f"  ✅ 无待结晶学习")
    
    # === 模块D: 记录进化日志 ===
    evo.write_to_file()
    
    # === 模块E: Sweep Delta 跟踪 (来自 Crucix) ===
    prev_state = state.get("sweep_state", {})
    sweep_delta = {}
    
    # 记录当前状态
    scripts_dir = os.path.join(KNOWLEDGE_DIR, "scripts")
    instincts_file = os.path.join(BASE_DIR, ".learnings", "INSTINCTS.md")
    learnings_file = os.path.join(BASE_DIR, ".learnings", "LEARNINGS.md")
    current_sweep = {
        "scripts": len([f for f in glob.glob(os.path.join(scripts_dir, "*.py"))]),
        "instincts": len(re.findall(r'## INS-\d+', open(instincts_file, 'r', encoding='utf-8').read())) if os.path.exists(instincts_file) else 0,
        "learnings": len(re.findall(r'## \[LRN-', open(learnings_file, 'r', encoding='utf-8').read())) if os.path.exists(learnings_file) else 0,
        "cat_files": len(glob.glob(os.path.join(STEAMDT_DIR, "*_排行榜.json"))),
    }
    
    delta_changed = {k: (prev_state.get(k), v) for k, v in current_sweep.items() 
                      if prev_state.get(k) is not None and prev_state[k] != v}
    if delta_changed:
        for k, (old, new) in delta_changed.items():
            print(f"  🔄 {k}: {old} → {new}")
    
    state["sweep_state"] = current_sweep
    
    # === 模块F: 更新 orchestrator state ===
    state["last_health"] = {
        "file_issues": len(file_issues),
        "enc_issues": len(enc_issues),
        "drift_candidates": len(drift_issues),
        "crystallizable": len(candidates),
        "timestamp": now.isoformat()
    }
    save_state(state)
    
    print(f"\n📊 运行摘要")
    print(evo.summaries())
    print(f"\n✅ 进化引擎 Gen #{gen} 完成")

if __name__ == "__main__":
    main()
