# 全境封锁2 配装计算器（网页版）

The Division 2 配装计算工具的网页版，纯静态单页应用，无需构建。

## 在线使用
部署在 Zeabur：见仓库 About 链接。

## 功能
- 双武器位 + 6 件装备配装（品牌/套装/具名/奇特），真实游戏渲染图与官方中文名
- 期望伤害 / 爆发 DPS / 循环 DPS / 弹匣伤害计算，暴击率 60% 上限提示
- 专精、手表、专精度、爆头率参数；条件天赋按「常驻/满层」口径
- 配装本地保存、JSON 导入导出、链接分享

## 文件
- `index.html` — 页面与计算引擎（对齐 mx-division-builds 的 statsService 公式）
- `data.js` — 由 `build_data.py` 生成（武器/装备/品牌/天赋数据 + 图标映射）
- `icons/` — 品牌/槽位图标与游戏渲染图（本地化，离线可用）
- `build_data.py` / `download_icons.py` — 数据管线：从 raw/ 的社区数据表生成 data.js 并下载图片
- `raw/` 不入库（第三方数据源，见下）

## 数据来源与致谢
- 数值表：[mx-division-builds](https://github.com/mxswat/mx-division-builds)（CC BY-NC-SA 4.0，DB 25.0-mdb）
- 渲染图与官方中文天赋：[td2-optimizer](https://github.com/Agent537-coder/td2-optimizer) 的 geardb
- 图标与游戏数据版权归 Ubisoft 所有；本工具为学习交流用途，非商业

## 更新数据
将数据源文件放入 `raw/` 后运行 `python3 build_data.py && python3 download_icons.py`，提交后 Zeabur 会自动重新部署。
