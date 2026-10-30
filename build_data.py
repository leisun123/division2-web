#!/usr/bin/env python3
"""Convert Mx Division Builds CSV data (DB 25.0-mdb) into a compact data.js for the calculator."""
import csv, json, os, re

RAW = os.path.join(os.path.dirname(os.path.abspath(__file__)), "raw")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.js")

ZH = {
    "Weapon Damage": "武器伤害",
    "Assault Rifle Damage": "突击步枪伤害",
    "LMG Damage": "轻机枪伤害",
    "Marksman Rifle Damage": "狙击步枪伤害",
    "Pistol Damage": "手枪伤害",
    "Rifle Damage": "射手步枪伤害",
    "Shotgun Damage": "霰弹枪伤害",
    "SMG Damage": "冲锋枪伤害",
    "Signature Weapon Damage": "专精武器伤害",
    "Explosive Damage": "爆炸伤害",
    "Critical Hit Chance": "暴击几率",
    "Critical Hit Damage": "暴击伤害",
    "Headshot Damage": "爆头伤害",
    "Damage to Armor": "对装甲伤害",
    "Damage to Health": "对生命伤害",
    "Damage to TOC": "对掩体外目标伤害",
    "Rate of Fire %": "射速",
    "Mag Size %": "弹匣容量",
    "Magazine Size %": "弹匣容量",
    "Reload Speed %": "换弹速度",
    "Weapon Handling": "操作性",
    "Stability": "稳定度",
    "Accuracy": "精准度",
    "Optimal Range": "有效射程",
    "Melee Damage": "近战伤害",
    "Ammo Capacity": "弹药容量",
    "Swap Speed": "收械速度",
    "% Armor": "总装甲加成",
    "Armor": "装甲",
    "Armor Regeneration": "装甲回复",
    "Armor Regeneration %": "装甲回复加成",
    "Armor on Kill": "击杀回甲",
    "Armor on Kill %": "击杀回甲",
    "Health": "生命值",
    "Health on Kill %": "击杀回血",
    "Hazard Protection": "危害防护",
    "Explosive Resistance": "爆炸抗性",
    "Incoming Repairs": "承受修复",
    "Protection from Elites": "精英防护",
    "Bleed Resistance": "流血抗性",
    "Blind Resistance": "致盲抗性",
    "Burn Resistance": "烧伤抗性",
    "Disrupt Resistance": "干扰抗性",
    "Shock Resistance": "电击抗性",
    "Skill Damage": "技能伤害",
    "Skill Haste": "技能加速",
    "Skill Duration": "技能持续时间",
    "Skill Health": "技能生命",
    "Skill Repair": "技能修复",
    "Repair Skills": "修复技能",
    "Status Effects": "状态效果",
    "Cooldown Reduction": "冷却缩减",
    "Skill Tier": "技能分阶",
    "Pulse Resistance": "脉冲抗性",
    "Pulse Haste": "脉冲加速",
    "Outgoing Healing": "治疗输出",
    "Burn Duration": "烧伤时间",
    "Extra Rounds": "额外弹药",
}
TYPE_ZH = {
    "Assault Rifle": "突击步枪", "SMG": "冲锋枪", "LMG": "轻机枪",
    "Rifle": "射手步枪", "Shotgun": "霰弹枪", "Marksman Rifle": "狙击步枪",
    "Pistol": "手枪",
}
SPEC_ZH = {
    "Sharpshooter": "精确射手", "Survivalist": "生存主义者",
    "Demolitionist": "爆破专家", "Gunner": "枪手",
    "Technician - Heals": "技师（治疗）", "Technician - Damage": "技师（输出）",
    "Firewall": "烈焰之墙",
}
QUALITY_ZH = {"High End": "金装", "Named": "具名", "Exotic": "奇特", "Gearset": "套装", "Prototype": "原型"}

def zh(stat):
    return ZH.get(stat, stat)

# ---------------------------------------------------------------- weapons
def num(x, alt=None):
    x = str(x).strip()
    if x:
        return float(x)
    if alt is not None:
        return alt
    raise ValueError("empty numeric field")

weapons = []
skipped = []
for r in csv.DictReader(open(os.path.join(RAW, "Weapons.csv"))):
    try:
        bk = r["Name"] == "Bullet King"
        core2 = {"stat": r["Core 2"], "max": num(r["Core 2 Max"])} if r["Core 2 Max"].strip() else None
        attr1 = r["Attribute 1"].strip()
        weapons.append({
            "name": r["Name"], "variant": r["Variant"], "type": r["Weapon Type"],
            "quality": r["Quality"],
            "dmg": num(r["Base Damage"]), "mag": int(num(r["Mag Size"], 999 if bk else None)),
            "rpm": int(num(r["RPM"])), "reload": int(num(r["Reload Speed (ms)"], 0 if bk else None)),
            "hsd": num(r["HSD"]),
            "core1": {"stat": r["Core 1"], "max": num(r["Core 1 Max"])},
            "core2": core2,
            "attr1": attr1 if attr1 != "A" else None,
            "talent": r["Talent"].strip() if r["Talent"].strip() not in ("", "A") else None,
        })
    except (ValueError, KeyError) as e:
        skipped.append((r.get("Name"), r.get("Variant"), str(e)))

# weapon attribute maxima (A tier) — used for weapon attr 1 when rollable
weapon_attr_pool = []
for r in csv.DictReader(open(os.path.join(RAW, "WeaponAttributes.csv"))):
    if r["Quality"] == "A" and r["Type"] == "O":
        weapon_attr_pool.append({"stat": r["Stat"], "max": float(r["Max"])})

# ---------------------------------------------------------------- brand / set bonuses
bonuses = {}
brand_names = set()
set_names = set()
for r in csv.DictReader(open(os.path.join(RAW, "BrandSetBonuses.csv"))):
    m = re.match(r"^(.*?)(\d)$", r["Brand"])
    name, idx = m.group(1), int(m.group(2))
    entry = {"stat": r["stat"], "val": float(r["val"])}
    bonuses.setdefault(name, {})[idx] = entry
    if r["stat"] not in ("Talent",):
        brand_names.add(name) if idx == 0 else None

# gear sets use suffix 1/2/3 (2/3/4 pieces); brands use 0/1/2 (1/2/3 pieces)
def is_set(name):
    return min(bonuses.get(name, {0: None}).keys()) >= 1

for name in list(bonuses.keys()):
    if is_set(name):
        set_names.add(name)
    else:
        brand_names.add(name)

# ---------------------------------------------------------------- gear slots
ICON = {
    "5.11 Tactical": "511", "Airaldi Holdings": "airaldi", "Alps Summit Armaments": "alps",
    "Badger Tuff": "badger", "Belstone Armory": "belstone", "Ceska Vyroba s.r.o.": "ceska",
    "China Light Industries Corporation": "china", "Douglas & Harding": "douglas",
    "Fenris Group AB": "fenris", "Gila Guard": "gila", "Golan Gear Ltd": "golan",
    "Grupo Sombra S.A.": "grupo", "Hana-U Corporation": "hanau",
    "Murakami Industries": "murakami", "Overlord Armaments": "overlord",
    "Petrov Defense Group": "petrov", "Providence Defense": "providence",
    "Richter & Kaiser GmbH": "richter", "Sokolov Concern": "sokolov",
    "Wyvern Wear": "wyvern", "Yaahl Gear": "yaahl", "Uzina Getica": "uzina",
    "Walker, Dunbar & Co.": "walker", "Brazos de Arcabuz": "brazos",
    "Empress International": "empress",
    "Aces and Eights": "aces", "Foundry Bullwark": "foundry", "Future Initiative": "umbra",
    "Hard Wired": "hotshot", "Negotiator's Dilemma": "negotiators",
    "Ongoing Directive": "ongoing", "Striker's Battlegear": "strikers",
    "System Corruption": "system", "Tip of the Spear": "hunters",
    "True Patriot": "true",
}
def icon_for(brand, kind):
    if kind == "exotic":
        return "exotic"
    return ICON.get(brand, "")

# talent effect modeling (additive wd / amplify amp / chc / chd / hsd / dta / mag)
GFX = {
    "Vigilance": {"wd": 25}, "Perfect Vigilance": {"wd": 25},
    "Composure": {"wd": 15}, "Companion": {"wd": 15},
    "Unstoppable Force": {"wd": 25},
    "Wicked": {"wd": 18}, "Perfectly Wicked": {"wd": 18},
    "Glass Cannon": {"amp": 25}, "Perfect Glass Cannon": {"amp": 30},
    "Intimidate": {"amp": 35}, "Perfect Intimidate": {"amp": 40},
    "Focus": {"wd": 50}, "Perfect Focus": {"wd": 60},
    "Obliterate": {"wd": 15},
    "Spotter": {"wd": 15},
    "Gunslinger": {"wd": 20},
    "Spark": {"wd": 15}, "Perfect Spark": {"wd": 15},
    "Overwatch": {"amp": 12}, "Perfect Overwatch": {"amp": 12},
    "Opportunistic": {"amp": 10},
    "Concussion": {"wd": 15},
}
WFX = {
    "Unhinged": {"wd": 18}, "Perfectly Unhinged": {"wd": 22},
    "Killer": {"chd": 40}, "Perfect Killer": {"chd": 50},
    "Strained": {"chd": 50}, "Perfect Strained": {"chd": 80},
    "Optimist": {"wd": 30}, "Perfect Optimist": {"wd": 40},
    "Overwhelm": {"wd": 40}, "Perfect Overwhelm": {"wd": 48},
    "Pumped Up": {"wd": 25}, "Perfect Pumped Up": {"wd": 25},
    "Close & Personal": {"wd": 30}, "Perfectly Close & Personal": {"wd": 38},
    "Eyeless": {"wd": 20}, "Perfect Eyless": {"wd": 25},
    "Ignited": {"wd": 20}, "Perfectly Ignited": {"wd": 25},
    "Sadist": {"wd": 20}, "Perfect Sadist": {"wd": 25},
    "Rifleman": {"wd": 50}, "Perfect Rifleman": {"wd": 50},
    "Swift": {"wd": 20},
    "Lucky Shot": {"mag": 20}, "Perfect Lucky Shot": {"mag": 30},
}

# gear talents by slot
gear_talents = {"Chest": [], "Backpack": []}
talent_desc = {}
for r in csv.DictReader(open(os.path.join(RAW, "GearTalents.csv"))):
    talent_desc[r["Talent"]] = r["Desc"]
    if r["Slot"] in gear_talents and r["Quality"] == "A":
        gear_talents[r["Slot"]].append({
            "name": r["Talent"], "desc": r["Desc"], "fx": GFX.get(r["Talent"]),
        })

# weapon talents
weapon_talents = []
seen_wt = set()
for r in csv.DictReader(open(os.path.join(RAW, "WeaponTalents.csv"))):
    name = r["Name"]
    if name in seen_wt or not r["Desc"]:
        continue
    seen_wt.add(name)
    types = [t for t, flag in (("Assault Rifle", r["Assault Rifle"]), ("Rifle", r["Rifle"]),
             ("Marksman Rifle", r["Marksman Rifle"]), ("SMG", r["SMG"]), ("LMG", r["LMG"]),
             ("Pistol", r["Pistol"]), ("Shotgun", r["Shotgun"])) if flag.strip()]
    weapon_talents.append({
        "name": name, "desc": r["Desc"], "types": types,
        "q": r["Quality"], "fx": WFX.get(name),
    })

# gear items per slot
slots = {}
for fname, slot in [("slot_Mask.csv", "Mask"), ("slot_Backpack.csv", "Backpack"),
                    ("slot_Chest.csv", "Chest"), ("slot_Gloves.csv", "Gloves"),
                    ("slot_Holster.csv", "Holster"), ("slot_Kneepads.csv", "Kneepads")]:
    items = []
    for r in csv.DictReader(open(os.path.join(RAW, fname))):
        q = r["Quality"]
        kind = {"High End": "brand", "Named": "named", "Gearset": "set", "Exotic": "exotic"}[q]
        items.append({
            "name": r["Item Name"] if kind in ("named", "exotic") else r["Brand"],
            "kind": kind, "brand": r["Brand"] if r["Brand"] != "Exotic" else None,
            "icon": icon_for(r["Brand"], kind),
            "talent": r["Talent"].strip() or None,
            "fixedTalent": kind in ("named", "exotic"),
        })
    slots[slot] = items

# gear attribute pools (secondary attributes), A and N tier
attrs = {"A": [], "N": []}
for r in csv.DictReader(open(os.path.join(RAW, "Attributes.csv"))):
    if r["Quality"] in ("A", "N"):
        attrs[r["Quality"]].append({"stat": r["Stat"], "max": float(r["Max"]), "type": r["Type"]})

mods = []
for r in csv.DictReader(open(os.path.join(RAW, "GearMods.csv"))):
    if r["Quality"] == "A" and r["Type"] == "O":
        mods.append({"stat": r["Stat"], "max": float(r["Max"])})

# specializations
specs = {}
for r in csv.DictReader(open(os.path.join(RAW, "Specialization.csv"))):
    specs.setdefault(r["Name"], []).append({"stat": r["Stat"], "val": float(r["Val"])})
spec_list = [{"name": k, "stats": v} for k, v in specs.items()]

# stat catalog actually used
used = set()
for b in bonuses.values():
    for e in b.values():
        used.add(e["stat"])
for a in attrs["A"] + attrs["N"]:
    used.add(a["stat"])
for w in weapons:
    used.add(w["core1"]["stat"])
    if w["core2"]:
        used.add(w["core2"]["stat"])
    if w["attr1"]:
        used.add(w["attr1"])
for m in mods:
    used.add(m["stat"])
for s in spec_list:
    for e in s["stats"]:
        used.add(e["stat"])
zh_map = {s: zh(s) for s in sorted(used)}

# ---------------------------------------------------------------- td2-optimizer geardb: icons + zh talents
import unicodedata

TDB_PATH = os.path.join(RAW, "geardb.json")
TREE_PATH = os.path.join(RAW, "td2tree.json")
tdb = json.load(open(TDB_PATH)) if os.path.exists(TDB_PATH) else None
repo_tree = {x["path"] for x in json.load(open(TREE_PATH))["tree"]} if os.path.exists(TREE_PATH) else set()
dl_list = []  # (repo_path, local_url)

def _iconfile(rel):
    """geardb icon 相对路径（如 weapon/xxx.png）→ (本地URL, 仓库路径)，webp 优先；跳过精灵图"""
    if not rel or not tdb or "spritesheet" in rel.lower():
        return None
    stem = "web/assets/db/img/" + rel[:-4]
    if stem + ".webp" in repo_tree:
        dl_list.append((stem + ".webp", "icons/gamedb/" + rel[:-4] + ".webp"))
        return "icons/gamedb/" + rel[:-4] + ".webp"
    if stem + ".png" in repo_tree:
        dl_list.append((stem + ".png", "icons/gamedb/" + rel[:-4] + ".png"))
        return "icons/gamedb/" + rel[:-4] + ".png"
    return None

def canon(s):
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return "".join(c for c in s.lower() if c.isalnum())

CANON_ALIAS = {
    "aceseights": "acesandeights",
    "alpssummitarmament": "alpssummitarmaments",
    "foundrybullwark": "foundrybulwark",
}
GEAR_TYPE_MAP = {
    "Assault Rifle": "Assault Rifle", "SMG": "Submachine Gun", "LMG": "Light Machine Gun",
    "Rifle": "Rifle", "Shotgun": "Shotgun", "Marksman Rifle": "Marksman Rifle", "Pistol": "Pistol",
}
def key(s):
    return canon(s)

def fuzzy_eq(a, b):
    ka, kb = key(a), key(b)
    return bool(ka and kb) and (ka == kb or ka in kb or kb in ka)

if tdb:
    # 官方中文名映射：品牌/套装（含缩写）
    brandZh = {}
    for b in tdb.get("brands", []):
        en = (b.get("en") or "").strip()
        if en:
            ck = CANON_ALIAS.get(canon(en), canon(en))
            brandZh[ck] = {"z": b.get("zh") or en, "a": b.get("abbr_zh") or ""}
    for en in list(brand_names) + list(set_names):
        ck = CANON_ALIAS.get(canon(en), canon(en))
        if ck in brandZh:
            brandZh[en] = brandZh.pop(ck)  # 以我们的 EN 名为键
    # 武器图标 + 官方中文名
    unmatched_w = []
    for w in weapons:
        t = GEAR_TYPE_MAP[w["type"]]
        cands = [x for x in tdb["weapons"] if (x.get("type_en") or "") == t]
        pool = [c for c in cands if fuzzy_eq(w["name"], c.get("en") or c.get("name"))]
        if w["quality"] == "Exotic":
            pool = [c for c in pool if c.get("exotic")] or pool
        elif w["quality"] == "Named":
            pool = [c for c in pool if c.get("named")] or pool
        else:
            pool = [c for c in pool if not c.get("exotic") and not c.get("named")] or pool
        pool.sort(key=lambda c: (c.get("named"), c.get("exotic")))  # 普通版优先
        if pool:
            w["zh"] = pool[0].get("zh") or pool[0].get("name") or w["name"]
            w["img"] = _iconfile(pool[0].get("icon")) or None
        else:
            unmatched_w.append(w["name"])
    # 装备图标 + 官方中文名（品牌件用中文品牌名，具名/奇特用品名）
    kindmap = {"brand": "brand", "set": "gearset", "named": "named", "exotic": "exotic"}
    unmatched_g = []
    for slot in slots:
        for it in slots[slot]:
            k = kindmap[it["kind"]]
            target = canon(it["brand"]) if k in ("brand", "gearset") else None
            target = CANON_ALIAS.get(target, target)
            hit = None
            for x in tdb["gear"]:
                if x.get("slot") != slot.lower() or x.get("kind") != k:
                    continue
                if k in ("named", "exotic"):
                    if fuzzy_eq(it["name"], x.get("en")):
                        hit = x
                        break
                else:
                    cb = canon(CANON_ALIAS.get(canon(x.get("brand_en")), x.get("brand_en")))
                    if cb == target:
                        hit = x
                        if x.get("gear_icon"):
                            break
            if hit:
                it["img"] = _iconfile(hit.get("gear_icon")) or None
                it["zh"] = (hit.get("zh") or hit.get("name")) if k in ("named", "exotic") else hit.get("brand")
            else:
                unmatched_g.append((slot, it["name"] or it["brand"]))
            # geardb 的官方天赋比 Mx CSV 新（如 Sawyer's 护膝应为坚守阵地），覆盖旧数据
            tl = hit.get("talent") if hit and isinstance(hit.get("talent"), dict) else None
            if tl and tl.get("en") and it.get("talent"):
                it["talent"] = tl["en"]
    # ---------- 补全：geardb 独有的奇特/原型/具名（武器与装备） ----------
    # 数值校准：按武器类型取 Mx基础伤害 / geardb面板伤害 的中位比值
    import statistics
    mx_base = {}
    for r in csv.DictReader(open(os.path.join(RAW, "Weapons.csv"))):
        try:
            mx_base[(canon(r["Name"]), r["Weapon Type"])] = float(r["Base Damage"])
        except Exception:
            pass
    ratios_by_type = {}
    for x in tdb["weapons"]:
        key = (canon(x.get("en") or ""), x.get("type_en"))
        if key in mx_base and x.get("dmg"):
            ratios_by_type.setdefault(x.get("type_en"), []).append(mx_base[key] / x["dmg"])
    type_ratio = {t: statistics.median(rs) for t, rs in ratios_by_type.items()}
    all_rs = sorted(v for rs in ratios_by_type.values() for v in rs)
    global_ratio = all_rs[len(all_rs) // 2] if all_rs else 0.84

    TYPE_FROM_GEARD = {"Assault Rifle": "Assault Rifle", "Submachine Gun": "SMG",
                       "Light Machine Gun": "LMG", "Rifle": "Rifle", "Shotgun": "Shotgun",
                       "Marksman Rifle": "Marksman Rifle", "Pistol": "Pistol"}
    existing_w = {(canon(w["name"]), w["type"]) for w in weapons}
    added_w = []
    # geardb 品质字段标 Grey 但实际是具名活动的枪（如丰收之人，本体特性+20%WD/-18%RPM 已含在 dmg/rpm）
    FORCE_NAMED = {"The Harvest"}
    # geardb 缺 rpm/mag 的家族（M44 全系无射速数据）→ 从本目录同型号基础枪借数值
    FAM_FILL = {"mosin_nagant": "Classic M44 Carbine"}
    for x in tdb["weapons"]:
        t_en = x.get("type_en")
        if t_en not in TYPE_FROM_GEARD:
            continue  # 跳过专精武器
        en = (x.get("en") or x.get("name") or "").strip()
        q = x.get("quality")
        if not (q in ("Exotic", "Prototype") or (q == "Orange" and x.get("named")) or (x.get("named") and en in FORCE_NAMED)):
            continue  # 只补奇特/原型/具名，灰色基础型号不收
        our_type = TYPE_FROM_GEARD[t_en]
        ck = (canon(en), our_type)
        if not en or ck in existing_w:
            continue
        existing_w.add(ck)
        if x.get("family") in FAM_FILL and (not x.get("rpm") or not x.get("mag")):
            b = next((w for w in weapons if w["name"] == FAM_FILL[x["family"]]), None)
            if b:
                x = dict(x, rpm=b["rpm"], mag=b["mag"], reload_ms=b["reload"],
                         head_mult=(b.get("hsd") or 0) / 100 + 1)
        if not x.get("dmg") or not x.get("rpm") or not x.get("mag"):
            continue
        k = type_ratio.get(t_en) or global_ratio
        tl = x.get("talent") if isinstance(x.get("talent"), dict) else None
        quality = {"Exotic": "Exotic", "Prototype": "Prototype"}.get(q, "Named")
        w = {
            "name": en, "variant": en, "type": our_type, "quality": quality,
            "zh": x.get("zh") or en,
            "dmg": round(x["dmg"] * k), "mag": int(x["mag"]), "rpm": int(x["rpm"]),
            "reload": int(x.get("reload_ms") or 2000), "hsd": round((x.get("head_mult") or 1.5) * 100 - 100),
            "core1": {"stat": {"Assault Rifle": "Assault Rifle Damage", "SMG": "SMG Damage", "LMG": "LMG Damage",
                               "Rifle": "Rifle Damage", "Shotgun": "Shotgun Damage",
                               "Marksman Rifle": "Marksman Rifle Damage", "Pistol": "Pistol Damage"}[our_type], "max": 15},
            "core2": None, "attr1": None,
            "talent": (tl.get("en") if tl and tl.get("en") else None),
            "img": _iconfile(x.get("icon")),
        }
        weapons.append(w)
        added_w.append(en)
        if tl and tl.get("en") and not any(t2["name"] == tl["en"] for t2 in weapon_talents):
            weapon_talents.append({"name": tl["en"], "desc": tl.get("desc_en") or "", "types": [our_type],
                                   "q": "N", "fx": WFX.get(tl["en"])})

    # 装备：补 geardb 独有的具名/奇特件
    added_g = []
    for slot in slots:
        have = {(canon(it.get("name") or ""), it["kind"]) for it in slots[slot]}
        for x in tdb["gear"]:
            if x.get("slot") != slot.lower() or x.get("kind") not in ("named", "exotic"):
                continue
            en = (x.get("en") or "").strip()
            k2 = x.get("kind")
            if not en or (canon(en), k2) in have:
                continue
            have.add((canon(en), k2))
            tl = x.get("talent") if isinstance(x.get("talent"), dict) else None
            brand_en = x.get("brand_en")
            it = {
                "name": en,
                "zh": x.get("zh") or en,
                "kind": k2,
                "brand": brand_en if (k2 == "named" and brand_en and brand_en != "-") else None,
                "icon": icon_for(x.get("brand_en"), k2),
                "talent": (tl.get("en") if tl and tl.get("en") else None),
                "fixedTalent": True,
                "img": _iconfile(x.get("gear_icon")),
            }
            slots[slot].append(it)
            added_g.append(en)
            if tl and tl.get("en") and tl not in (None,):
                pass
    # geardb 装备天赋也补进 zh 映射源（talent dict 自带 zh/icon 的场景）

    # 天赋中文名/中文描述/图标（按英文名匹配）
    talent_zh = {}
    for x in tdb["talents_official"]:
        en = (x.get("en") or "").strip()
        if not en or en.lower() in talent_zh:
            continue
        entry = {
            "z": x.get("zh") or en,
            "d": (x.get("desc_filled_zh") or x.get("desc_zh") or "").strip(),
        }
        ic = _iconfile(x.get("icon")) if x.get("icon") else None
        if ic:
            entry["i"] = ic
        if entry["d"] or entry.get("i"):
            talent_zh[en.lower()] = entry

    def base_lookup(en):
        k = en.lower()
        if k in talent_zh:
            return talent_zh[k]
        for pre in ("perfect ", "perfectly "):
            if k.startswith(pre):
                b = talent_zh.get(k[len(pre):])
                if b:
                    merged = dict(b)
                    merged["z"] = "完美" + b["z"]
                    return merged
        return None
else:
    unmatched_w = unmatched_g = []
    def base_lookup(en):
        return None

talent_zh_out = {}
for t in weapon_talents + [x for s in gear_talents.values() for x in s]:
    r = base_lookup(t["name"]) if tdb else None
    if r:
        talent_zh_out[t["name"].lower()] = r
# 具名/异域固定天赋也补查一遍
fixed_names = {it["talent"] for slot in slots for it in slots[slot] if it.get("talent")}
for n in fixed_names:
    if n and n.lower() not in talent_zh_out:
        r = base_lookup(n) if tdb else None
        if r:
            talent_zh_out[n.lower()] = r
# 武器的固定天赋同样补查（如雪橇弑手的 Hidden Rock 不在 Mx 天赋清单里）
w_fixed = {w.get("talent") for w in weapons if w.get("talent")}
for n in w_fixed:
    if n and n.lower() not in talent_zh_out:
        r = base_lookup(n) if tdb else None
        if r:
            talent_zh_out[n.lower()] = r

if tdb:
    dl_list = sorted(set(dl_list))
    with open(os.path.join(RAW, "dl.txt"), "w") as f:
        for rp, lp in dl_list:
            f.write(rp + "\t" + lp + "\n")

data = {
    "version": open(os.path.join(RAW, "DB.Version")).read().strip(),
    "zh": zh_map, "typeZh": TYPE_ZH, "qualityZh": QUALITY_ZH,
    "weapons": weapons, "weaponAttrPool": weapon_attr_pool,
    "weaponTalents": weapon_talents,
    "bonuses": bonuses, "brandNames": sorted(brand_names), "setNames": sorted(set_names),
    "brandZh": brandZh if tdb else {},
    "slots": slots, "gearTalents": gear_talents, "talentDesc": talent_desc,
    "attrs": attrs, "mods": mods,
    "specs": spec_list,
    "specZh": SPEC_ZH,
    "talentZh": talent_zh_out,
}
js = "window.D2 = " + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n"
open(OUT, "w", encoding="utf-8").write(js)
print("data.js written:", round(os.path.getsize(OUT) / 1024), "KB")
print("weapons:", len(weapons), "| slots:", {k: len(v) for k, v in slots.items()},
      "| gearTalents:", {k: len(v) for k, v in gear_talents.items()},
      "| weaponTalents:", len(weapon_talents), "| brands:", len(brand_names), "| sets:", len(set_names))
if skipped:
    print("skipped weapon rows:", skipped)
if tdb:
    nw = sum(1 for w in weapons if w.get("img"))
    ng = sum(1 for s in slots for it in slots[s] if it.get("img"))
    print(f"图标匹配: 武器 {nw}/{len(weapons)} | 装备 {ng}/{sum(len(v) for v in slots.values())} | 需下载 {len(dl_list)} 个文件")
    if unmatched_w:
        print("未匹配武器:", unmatched_w[:15])
    if unmatched_g:
        print("未匹配装备:", unmatched_g[:20])
    print("天赋中文映射:", len(talent_zh_out))
    print("geardb 补全: 武器 +%d (%s...) | 装备 +%d" % (len(added_w), ",".join(added_w[:5]), len(added_g)))
