# Project Plan：Portfolio Analytics Suite

## 0. 项目定位

一个多工具的投资组合分析系列应用，通过 Streamlit 多 Tab 页面集成。当前版本包含两个功能模块：

| Tab   | 名称                 | 核心功能                          |
| ----- | ------------------ | ----------------------------- |
| Tab 1 | 动态相关性追踪            | 基于 GARCH + 卡尔曼滤波的时变相关性矩阵      |
| Tab 2 | Efficient Frontier | 基于动态相关性的均值-方差前沿优化             |
| Tab 3 | 方法论文档              | 面向业务用户的方法论说明页，解释工具的核心逻辑和设计决策。 |

两个 Tab 共享同一套数据层和相关性计算结果，Tab 2 直接复用 Tab 1 的最新期动态 ρ 矩阵。

---

## 1. 系统架构

```
portfolio_analytics/
│
├── app.py                      # Streamlit 主入口，定义两个 Tab
│
├── core/
│   ├── __init__.py
│   ├── data_loader.py          # yfinance 数据拉取与缓存
│   ├── garch_filter.py         # GARCH(1,1) 标准化
│   ├── kalman_filter.py        # 一维卡尔曼滤波
│   ├── correlation.py          # 主计算流水线，输出三频矩阵
│   └── optimizer.py            # 均值-方差优化，输出有效前沿
│
├── ui/
│   ├── __init__.py
│   ├── matrix_view.py          # 相关性矩阵热力图组件
│   ├── timeseries_view.py      # ρ 时间序列图组件
│   └── frontier_view.py        # Efficient Frontier 图组件
│
├── config/
│   └── assets.yaml             # 可配置资产列表
│
└── requirements.txt
```

---

## 2. Tab 1：动态相关性追踪

### 2.1 核心技术决策（已确认）

| 决策点 | 选择 | 理由 |
|--------|------|------|
| 状态转移系数 φ | **1.0**（随机游走） | 不引入均值回复假设，与物理 KF 哲学一致 |
| 观测值 Obs | **$\tilde{X}_t \times \tilde{Y}_t$**（标准化收益率乘积） | 满足测量方程线性假设，无偏估计 ρ |
| 边界处理 | **np.clip([-1, 1])** | 工程优先，若长期触边再调模型 |
| Q / R 参数 | 开发阶段调试确定 | 先跑通，后调优 |

### 2.2 数学模型

**GARCH 标准化**

$$\tilde{X}_t = \frac{r^X_t}{\sigma^X_t}, \quad \tilde{Y}_t = \frac{r^Y_t}{\sigma^Y_t}$$

**观测值构造**

$$\text{Obs}_t = \tilde{X}_t \times \tilde{Y}_t$$

**状态空间方程**

$$\rho_t = \rho_{t-1} + \eta_t, \quad \eta_t \sim \mathcal{N}(0, Q)$$

$$\text{Obs}_t = \rho_t + \epsilon_t, \quad \epsilon_t \sim \mathcal{N}(0, R)$$

**卡尔曼递推**

$$\hat{\rho}_{t|t-1} = \hat{\rho}_{t-1|t-1}, \quad P_{t|t-1} = P_{t-1|t-1} + Q$$

$$K_t = \frac{P_{t|t-1}}{P_{t|t-1} + R}$$

$$\hat{\rho}_{t|t} = \hat{\rho}_{t|t-1} + K_t \left(\text{Obs}_t - \hat{\rho}_{t|t-1}\right), \quad P_{t|t} = (1 - K_t) \cdot P_{t|t-1}$$

$$\rho_t^{\text{final}} = \text{clip}(\hat{\rho}_{t|t},\ -1.0,\ 1.0)$$

### 2.3 UI 设计

**Sidebar（两个 Tab 共用）**
- 多选框选择资产（ticker + 中文名 + 分组）
- 日期范围选择器（默认过去 5 年）
- Q / R 参数滑块（可折叠，调试用）
- "Run" 按钮触发计算

**主区域**
- 三个子 Tab：日频 / 周频 / 月频
- 每个子 Tab：Plotly 热力图，红（-1）→ 白（0）→ 蓝（1），显示数值
- 点击任意单元格 → 页面下方展开该资产对的 ρ 时间序列
  - 日/周/月三频曲线叠加，不同颜色
  - ±1 边界参考线
  - 最新 ρ 值标注
  - 原始 Obs 散点（半透明）

---

## 3. Tab 2：Efficient Frontier

### 3.1 数据流

```
Tab 1 计算结果
    └── 最新一期动态 ρ 矩阵（月频）
            └── 作为协方差矩阵的相关性输入
                    └── 结合用户输入的 Forward σ
                            └── 构建协方差矩阵 Σ
                                    └── 结合用户输入的 Forward μ
                                            └── 均值-方差优化 → EF
```

协方差矩阵构造：

$$\Sigma_{ij} = \rho_{ij}^{\text{KF}} \cdot \sigma_i^{\text{fwd}} \cdot \sigma_j^{\text{fwd}}$$

### 3.2 用户输入

**Forward Return（μ）和 Forward Sigma（σ）输入方式**

- **历史自动填充**：点击"从历史数据填充"按钮，自动计算各资产在所选时间范围内的年化历史均值收益率和年化历史波动率，预填充到输入表格
- **手动覆盖**：用户可在表格中直接编辑任意资产的 μ 和 σ，手动输入的单元格高亮显示以示区分
- 输入表格列：Ticker | 名称 | Forward μ (%) | Forward σ (%) | 是否允许做空

**其他控制项**
- 资产多选（默认全选当前已计算资产）
- 是否允许做空（全局开关，也可按资产单独设置）
- 无风险利率输入（用于计算夏普率，默认 4.5%）

### 3.3 优化目标与约束

使用 `scipy.optimize.minimize` 求解：

**目标一：最大化夏普率（Max Sharpe）**

$$\max_w \frac{w^\top \mu - r_f}{\sqrt{w^\top \Sigma w}}$$

**目标二：最小化波动率（Min Vol）**

$$\min_w \sqrt{w^\top \Sigma w}$$

**约束**
- $\sum_i w_i = 1$（权重归一）
- 不允许做空时：$w_i \geq 0$；允许做空时：$w_i \geq -0.5$

**协方差矩阵数值保护**

$$\Sigma_{\text{reg}} = \Sigma + \lambda I, \quad \lambda = 1\text{e-6}$$

当两个资产相关性极高时（如 SPY/QQQ，ρ ≈ 0.98），Σ 接近奇异矩阵，求逆时数值不稳定，优化器可能崩溃或输出极端权重。加 λI 给对角线补一个极小值，强行保证矩阵满秩。λ 足够小，不改变经济含义。

### 3.4 有效前沿生成算法

均值-方差优化是**凸优化问题**（允许做空时严格凸，加非负约束后仍凸），目标函数和约束均为凸，因此不需要 Pareto 启发式搜索（NSGA-II 等遗传算法），而是使用**参数化扫描法**：

1. 计算收益率可行范围：$[\mu_{\min},\ \mu_{\max}]$（Min Vol 组合收益率到最高单资产收益率）
2. 在此范围内均匀取 **100 个目标收益率** $\bar{\mu}_k$
3. 对每个 $\bar{\mu}_k$，求解约束最小方差问题：

$$\min_w \ w^\top \Sigma w \quad \text{s.t.} \quad w^\top \mu = \bar{\mu}_k,\ \sum_i w_i = 1,\ w_i \geq \text{lb}$$

4. 100 个解 $(\sigma_k, \bar{\mu}_k)$ 连线即为有效前沿曲线

此方法解析结构干净，100 个点计算耗时 < 1s。Pareto 优化留待未来引入非线性多目标（如同时优化因子暴露）时再考虑。

### 3.4 UI 设计

**图表区域（Plotly 交互图）**
- 横轴：年化波动率（%），纵轴：年化预期收益率（%）
- 展示内容：
  - 有效前沿曲线（主线，颜色按夏普率渐变）
  - Max Sharpe 点（星形标注）
  - Min Vol 点（菱形标注）
  - 用户自定义组合点（见下方）
  - 各资产单独点（散点，hover 显示 ticker）

**点击前沿**
- 点击前沿上任意点 → 右侧面板展示该点的组合权重（横向条形图）
- 权重正负用不同颜色区分（多头蓝，空头红）

**用户自定义组合**
- 页面底部提供权重输入表格（各资产权重，必须合计为 100%）
- 实时校验权重合计，不为 100% 时显示红色提示
- 输入完成后点击"Plot"→ 将该组合作为一个单独的点画在 EF 图上
- 显示该组合的预期收益率、波动率、夏普率

---

## 4. 开发任务分解

### Phase 1：数据与核心计算层（预计 2 天）

**Task 1.1 — 数据拉取（data_loader.py）**
- 接受 ticker 列表和时间范围
- `yfinance.download()` 拉取收盘价，计算对数收益率
- 本地 parquet 缓存（`/tmp/ticker_start_end.parquet`）
- 缺失值：前向填充，超过 5 个连续缺失则报警
- **日期对齐**：取各 ticker 有效数据的交集区间；若短于用户请求区间，黄色提示框说明瓶颈 ticker（当前默认资产 5 年不触发，为未来自定义资产预留）

**Task 1.2 — GARCH 过滤（garch_filter.py）**
- `arch` 库拟合 GARCH(1,1)，提取条件波动率 $\sigma_t$
- 返回标准化收益率 $\tilde{r}_t = r_t / \sigma_t$
- 边界保护：$\sigma_t < 1\text{e-8}$ 时回退到全局标准差
- GARCH 不收敛时捕获异常，回退到滚动标准差，UI 提示该资产

**Task 1.3 — 卡尔曼滤波（kalman_filter.py）**
- 输入：`obs`（numpy array），`Q`、`R`、`rho_init=0.0`、`P_init=1.0`
- 输出：滤波后 ρ 序列
- 默认参数：`Q=0.001`，`R=0.5`

**Task 1.4 — 主流水线（correlation.py）**
- 对每对 (i, j) 执行 GARCH → Obs → KF
- 支持日频 / 周频（每周最后交易日）/ 月频（每月最后交易日）
- 输出：`Dict[freq, DataFrame(matrix)]` 和 `Dict[(i,j), Dict[freq, Series(rho_t)]]`
- 并行：`ThreadPoolExecutor` 加速 GARCH 拟合和资产对计算

**Task 1.5 — 优化器（optimizer.py）**
- 输入：`mu`（array）、`sigma`（array）、`rho_matrix`（DataFrame，最新期月频）、`rf`、`allow_short`
- 构建协方差矩阵 Σ
- 实现 Max Sharpe、Min Vol 两个求解函数
- 扫描 100 个目标收益率点，生成完整前沿
- 输出：前沿点集（vol, ret, weights）、Max Sharpe 点、Min Vol 点

### Phase 2：Streamlit UI（预计 3 天）

**Task 2.1 — 主框架（app.py）**
- 顶部 Tab 切换：Tab 1 / Tab 2
- 左侧 Sidebar 共用：资产选择、日期范围、Q/R 滑块、Run 按钮
- `st.session_state` 管理计算结果，两个 Tab 共享

**Task 2.2 — Tab 1 矩阵视图（matrix_view.py）**
- 三个子 Tab（日/周/月），Plotly 热力图
- `clickData` + `st.session_state` 实现点击回调

**Task 2.3 — Tab 1 时间序列视图（timeseries_view.py）**
- 点击矩阵后展开，三频曲线 + Obs 散点

**Task 2.4 — Tab 2 输入面板**
- 资产选择、做空开关、无风险利率
- μ / σ 输入表格：历史自动填充按钮 + 手动覆盖（手动修改单元格高亮）
- 权重输入表格（自定义组合）：实时合计校验

**Task 2.5 — Tab 2 前沿视图（frontier_view.py）**
- Plotly 散点图：前沿曲线 + Max Sharpe + Min Vol + 各资产点 + 用户自定义组合点
- 点击前沿点 → 右侧权重条形图
- 用户自定义组合点：显示预期收益率 / 波动率 / 夏普率

### Phase 3：配置与工程收尾（预计 1 天）

**Task 3.1 — 资产配置文件（assets.yaml）**

```yaml
assets:
  - ticker: "QQQ"
    name: "纳斯达克100ETF"
    group: "美股权益"
  - ticker: "SPY"
    name: "标普500ETF"
    group: "美股权益"
  - ticker: "IWM"
    name: "罗素2000ETF"
    group: "美股权益"
  - ticker: "COWZ"
    name: "现金流ETF"
    group: "美股权益"
  - ticker: "GLD"
    name: "黄金ETF"
    group: "商品"
  - ticker: "STIP"
    name: "短期TIPS ETF"
    group: "固收"
  - ticker: "TLT"
    name: "20年期美债ETF"
    group: "固收"
  - ticker: "SHY"
    name: "短期美债ETF"
    group: "固收"
  - ticker: "BTC-USD"
    name: "比特币"
    group: "加密"
  - ticker: "ETH-USD"
    name: "以太坊"
    group: "加密"
```

**Task 3.2 — 依赖与环境**

```
# requirements.txt
streamlit>=1.35
yfinance>=0.2.40
arch>=6.3
numpy>=1.26
pandas>=2.2
plotly>=5.22
scipy>=1.13
pyyaml>=6.0
pyarrow>=16.0
```

**Task 3.3 — 性能优化**
- `@st.cache_data` 装饰数据拉取和 GARCH 计算（TTL=1h）
- `ThreadPoolExecutor` 并行 GARCH 拟合和资产对 KF 计算

---

## 5. 关键风险与应对

| 风险 | 具体表现 | 应对措施 |
|------|----------|----------|
| GARCH 不收敛 | 某资产波动率极低或数据不足 | 捕获异常，回退到滚动标准差，UI 提示 |
| ρ 长期钉在 ±1 | Q/R 设置不当 | Phase 3 前手动调参，记录可用范围 |
| yfinance 限速 | 资产多、历史长时拉取失败 | 分批请求 + parquet 缓存 |
| Plotly 点击回调 | clickData 在 Streamlit 中实现繁琐 | `st.session_state` 管理选中状态 |
| 优化器不收敛 | μ/σ 输入极端或资产高度共线 | 捕获异常，提示用户检查输入；对协方差矩阵加微小正则项 $\Sigma + \lambda I$ |
| 权重表格合计校验 | 用户输入不为 100% | 实时红色提示，禁用 Plot 按钮直到合计有效 |

---

## 6. 开发顺序建议

```
Week 1
  Day 1-2:  Task 1.1 ~ 1.4（相关性计算层，Jupyter 验证 SPY/GLD 单对效果）
  Day 3:    Task 1.5（优化器，Jupyter 验证 EF 曲线形状合理性）
  Day 4-5:  Task 2.1 ~ 2.3（Tab 1 UI）

Week 2
  Day 1-2:  Task 2.4 ~ 2.5（Tab 2 UI）
  Day 3:    Task 3.1 ~ 3.3（配置、缓存、并行、收尾）

验收标准
  Tab 1
  □ 10 个默认资产，5 年日频，首次计算 60s 内完成
  □ 三频矩阵正确展示，数值在 [-1, 1]
  □ 点击单元格，ρ 时间序列正确渲染，含 Obs 散点
  □ Q/R 滑块调整后曲线刷新

  Tab 2
  □ 历史自动填充正确计算年化 μ 和 σ
  □ 手动修改单元格后高亮显示
  □ EF 曲线形状合理（不允许做空时前沿明显收窄）
  □ 点击前沿点，权重条形图正确渲染
  □ 自定义组合点正确落在图上，夏普率计算正确
  □ 权重不为 100% 时 Plot 按钮禁用
```

---


---

## 7. Tab 3：方法论文档

### 7.1 定位

面向业务用户的方法论说明页，解释工具的核心逻辑和设计决策。风格以直觉类比为主，公式为辅，中英双语通过语言切换按钮控制。在 Streamlit 中以 `st.markdown` + `st.latex` 渲染静态内容，无需交互。

### 7.2 文档结构与内容纲要

**Section 1 — 为什么相关性会变化？**
*Why Does Correlation Change Over Time?*

静态相关系数的局限：用单一数字描述两个资产的关系，就像用年均气温描述一座城市的气候——信息量严重不足。市场压力期（如 2020 年 3 月）资产间相关性会骤然上升，平静期又会下降。本工具的目标是实时追踪这个动态变化。

**Section 2 — 我们如何剥离波动率干扰（GARCH）**
*Removing Volatility Noise: The GARCH Filter*

直觉类比：两个运动员的配合默契程度，不应该因为比赛强度高低而失真。GARCH 把"比赛强度"（市场波动率）标准化掉，让我们看到纯粹的协同关系，而不是被波动率放大或压缩的假象。公式作为补充展示，不作为重点。

**Section 3 — 卡尔曼滤波：有记忆的观测者**
*The Kalman Filter: A Self-Updating Belief*

直觉类比：你每天观察天气，形成对"这座城市天气规律"的判断。每次新的观测，你不会完全推翻之前的判断，也不会完全忽视新数据——你会按照自己对观测可靠性的信心，把新旧信息加权融合。卡尔曼滤波做的正是这件事。

解释三个核心概念：
- **ρ（隐藏状态）**：我们真正想知道的相关性，无法直接观测
- **Obs（噪声观测）**：每期看到的原始信号，含大量随机噪声
- **P（不确定性）**：模型对自己当前估计有多少把握，动态自适应

说明 φ=1 的设计选择：不假设相关性会回归任何固定水平，让数据自己说话。

**Section 4 — Efficient Frontier：在约束下寻找最优权衡**
*Efficient Frontier: The Best Possible Trade-off*

直觉类比：在固定预算内搭配食材，既要营养均衡又要口味好——有效前沿就是所有"不可能做得更好"的组合的集合。任何偏离前沿的组合，都意味着在同样风险下放弃了收益，或在同样收益下承担了多余风险。

说明两个关键输入：
- **Forward μ**：你对未来收益的预判，工具提供历史均值作为起点，鼓励用户结合自己判断覆盖
- **Forward σ**：你对未来波动的预判，同上

说明动态 ρ 如何接入：协方差矩阵使用卡尔曼滤波输出的最新期相关性，而非历史静态值，使优化结果反映当前市场结构。

**Section 5 — 模型局限性与使用注意**
*Model Limitations*

- 卡尔曼滤波假设相关性变化是线性渐进的，对突发性结构断裂（如市场崩溃第一天）反应有滞后
- Forward μ 和 σ 的质量决定 EF 的质量，历史自动填充仅为参考起点，不构成预测
- 允许做空的 EF 结果对参数更敏感，空头权重上限 -50% 是工程约束，非最优理论边界
- GARCH 在极低波动率资产上可能不收敛，此时回退到滚动标准差，页面会有提示

### 7.3 实现方式

- 内容以 Markdown 文件形式维护（`docs/methodology_zh.md` + `docs/methodology_en.md`），与代码解耦，便于后续修改
- Tab 3 通过 `st.radio` 语言切换按钮控制显示中文或英文版本
- 公式用 `st.latex` 渲染
- 每个 Section 用 `st.expander` 包裹，默认展开 Section 1-2，其余折叠，避免页面过长

### 7.4 文件结构补充

```
portfolio_analytics/
│
├── docs/
│   ├── methodology_zh.md       # 中文方法论文档
│   └── methodology_en.md       # 英文方法论文档
│
└── ui/
    └── methodology_view.py     # Tab 3 渲染组件
```

---

## 8. 后续扩展方向（不在当前 scope）

- **参数自动估计**：EM 算法估计 Q、R
- **Fisher Z 变换**：若频繁触边再引入
- **Black-Litterman**：在 EF Tab 基础上叠加观点矩阵
- **组合回测 Tab**：将选定权重做历史回测，输出净值曲线和归因
- **报警机制**：相关性突破历史分位数时触发通知

---

## 9. Todo List

### Phase 1 — 数据与核心计算层

- [ ] **data_loader.py** — yfinance 拉取、parquet 缓存、日期对齐、缺失值处理
- [ ] **garch_filter.py** — GARCH(1,1) 拟合、条件波动率、不收敛回退逻辑
- [ ] **kalman_filter.py** — 一维 KF 递推、φ=1、np.clip 边界处理
- [ ] **correlation.py** — 主流水线：日/周/月三频矩阵、ThreadPoolExecutor 并行
- [ ] **optimizer.py** — Max Sharpe & Min Vol、参数化扫描 100 点生成 EF、Σ+λI 正则化

### Phase 2 — Streamlit UI

- [ ] **app.py 主框架** — 三 Tab 骨架、共用 Sidebar、st.session_state 状态管理
- [ ] **matrix_view.py** — 日/周/月热力图、Plotly clickData 回调
- [ ] **timeseries_view.py** — 三频 ρ 曲线叠加、Obs 散点、±1 参考线
- [ ] **Tab 2 输入面板** — μ/σ 表格、历史自动填充、手动高亮覆盖、做空开关
- [ ] **frontier_view.py** — EF 曲线、Max Sharpe/Min Vol 标注、自定义组合点、权重条形图
- [ ] **methodology_view.py** — Tab 3 中英双语、st.expander 分节、st.latex 公式渲染

### Phase 3 — 配置与工程收尾

- [ ] **assets.yaml** — 10 个默认资产：QQQ SPY IWM COWZ GLD STIP TLT SHY BTC ETH
- [ ] **requirements.txt** — streamlit yfinance arch numpy pandas plotly scipy pyyaml pyarrow
- [ ] **docs/methodology_zh.md + en.md** — 5 节方法论文档，业务风格，中英双语
- [ ] **性能优化** — @st.cache_data TTL=1h、ThreadPoolExecutor 并行验收

### 验收测试

- [ ] Tab 1 — 10 资产 5 年日频，首次计算 60s 内完成
- [ ] Tab 1 — 三频矩阵数值全部在 [-1, 1]，无 NaN
- [ ] Tab 1 — 点击单元格，ρ 时间序列含 Obs 散点正确渲染
- [ ] Tab 1 — Q/R 滑块调整后曲线实时刷新，无长期 ±1 钉死
- [ ] Tab 2 — 历史填充正确年化，手动修改单元格高亮
- [ ] Tab 2 — 前沿形状合理，不允许做空时明显收窄
- [ ] Tab 2 — 点击前沿点权重图正确，自定义组合夏普率正确，权重≠100% 时禁用 Plot
- [ ] Tab 3 — 中英切换正常，公式渲染，Expander 默认状态正确
