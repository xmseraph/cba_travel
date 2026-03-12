# CBA 2025-26 赛季球队旅行里程分析

对中国男子篮球职业联赛（CBA）2025-26 赛季各球队旅行里程的分析，包括赛程优化以减少总旅行距离。

## 项目概述

本项目：

1. 收集 CBA 各球队所在城市及地理坐标
2. 使用 Haversine 公式计算每支球队每轮比赛的旅行公里数
3. 在保留所有对阵的前提下优化赛程，减少总旅行公里数
4. 计算无约束条件下的理论最低旅行公里数作为参照
5. 通过 Streamlit 交互式仪表盘进行可视化展示

## 数据文件

| 文件 | 说明 |
|------|------|
| `cba_teams_2025_26.csv` | 20 支 CBA 球队，包含分区、城市、省份、经纬度 |
| `cba_schedule_2025_26.csv` | 完整赛季赛程（420 场比赛，42 轮），数据来自新浪体育 |
| `cba_schedule_optimized_2025_26.csv` | 优化后的赛程（相同比赛重新分配到各轮） |
| `cba_travel_mileage_2025_26.csv` | 原始旅行公里数（宽格式：轮次 × 球队） |
| `cba_travel_mileage_optimized_2025_26.csv` | 优化后旅行公里数（宽格式） |
| `cba_travel_detail_2025_26.csv` | 原始旅行明细（长格式：球队、轮次、公里数、出发/到达城市） |
| `cba_travel_detail_optimized_2025_26.csv` | 优化后旅行明细（长格式） |
| `cba_travel_lower_bound.csv` | 各球队无约束理论最低公里数 |

## 脚本说明

### `gen_travel_mileage.py`

读取球队坐标和赛程数据，计算每支球队每轮的旅行公里数。跟踪球队当前所在位置，使用 Haversine 公式计算到下一个比赛场馆的距离。

**输出：** `cba_travel_mileage_2025_26.csv`（宽格式）和 `cba_travel_detail_2025_26.csv`（长格式，含出发/到达城市）。

```
python gen_travel_mileage.py
```

### `analyze_schedule.py`

分析原始赛程的旅行公平性：各球队总公里数、对阵频次、连续客场长度、分区对比等。

```
python analyze_schedule.py
```

### `optimize_schedule.py`

在保留完全相同的 420 场比赛（相同主客场对阵及场次）的前提下，重新分配比赛到各轮以最小化总旅行公里数。采用三阶段算法：

1. **边着色（Edge Coloring）** — 将比赛分配到各轮，确保每支球队每轮只打一场
2. **贪心轮次排序** — 对 42 轮进行排序以最小化累计旅行距离
3. **局部搜索优化** — 在轮次间交换比赛，在保持合法性的前提下进一步减少公里数

**结果：** 总旅行公里数减少 20.4%（700,218 → 557,383 公里），极差缩小 60%（32,184 → 12,796 公里）。

**输出：** `cba_schedule_optimized_2025_26.csv`、`cba_travel_mileage_optimized_2025_26.csv`、`cba_travel_detail_optimized_2025_26.csv`。

```
python optimize_schedule.py
```

### `analyze_lower_bound.py`

计算各球队在无赛程约束条件下的理论旅行公里数下界（假设每支球队可以自由安排 42 场比赛顺序）。使用最近邻 + 2-opt 启发式算法（TSP 类方法）。

**输出：** `cba_travel_lower_bound.csv`

```
python analyze_lower_bound.py
```

### `travel_app.py`

Streamlit 交互式仪表盘，包含：

- **三个标签页：** 原始赛程、优化赛程、对比视图
- **折线图：** 展示每轮旅行公里数，悬停提示包含球队、轮次、公里数、出发/到达城市
- **汇总表：** 原始公里数、优化公里数、无约束下界、节省公里数及效率指标
- 球队多选功能，颜色动态分配

```
streamlit run travel_app.py
```

## 环境配置

```bash
# 创建虚拟环境（Python 3.12）
python -m venv .venv

# 激活虚拟环境（Windows PowerShell）
.venv\Scripts\Activate.ps1

# 安装依赖
pip install streamlit pandas altair

# 按顺序生成数据
python gen_travel_mileage.py
python optimize_schedule.py
python analyze_lower_bound.py

# 启动仪表盘
streamlit run travel_app.py
```

## 主要发现

| 指标 | 原始赛程 | 优化赛程 | 变化 |
|------|----------|----------|------|
| 总旅行公里数（全部球队） | 700,218 公里 | 557,383 公里 | -20.4% |
| 单队最高（新疆飞虎） | 57,424 公里 | 26,982 公里 | -53.0% |
| 单队最低 | 25,240 公里 | 22,244 公里 | -11.9% |
| 极差（最高 − 最低） | 32,184 公里 | 12,796 公里 | -60.2% |
| 无约束理论下界 | — | 174,560 公里 | — |

## 数据来源

赛程数据来自[新浪体育 CBA](https://cba.sports.sina.com.cn)。
