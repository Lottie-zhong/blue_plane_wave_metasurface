# 当前课题最新方案备忘录

## 一、课题总定位

本课题不再简单定位为：

> Micro-LED + metasurface + circularly polarized emission

原因是课题组前期 Gao 2021 已经实现 GaN Micro-LED 集成功能超表面产生圆偏振光，用于 3D display。该路线采用 Al 纳米光栅实现线偏振输出，再用 TiO2 nanobrick metasurface 作为四分之一波片，将线偏振转为圆偏振。

当前课题应升级为：

> 自旋选择性圆偏振定向出光

更具体地说：

- LCP -> RCP, +15 deg
- RCP -> 非目标角度、非目标衍射级、反射或少量损耗

目标不是把全部非偏振光无损变成一个圆偏振光束，而是：

> 从非偏振发光中选择一个圆偏振通道，并将其定向提取到目标方向。

## 二、核心物理逻辑

非偏振光可以表示为两个正交圆偏振态的非相干等权混合：

```text
I_unpol = 1/2 I_LCP + 1/2 I_RCP
```

所以超表面可以设计成：

```text
LCP_in -> RCP_out, +15 deg
RCP_in -> non-target channels
```

最终目标方向输出主要来自 LCP 那一半输入能量。

这个逻辑与 Taguchi 2026 的思想相关：该文指出典型 (0001) InGaN LED 表面发射是非偏振的，并设计单层 GaN metasurface 从非偏振 LED 发光中选择一个圆偏振分量；同时指出从任意无 CP 成分的偏振态转换到圆偏振态的效率上限为 50%。

本课题的进一步创新点是：

> 圆偏振选择 + 角度选择 + opposite spin redistribution

## 三、阶段一：平面波自旋选择性 beam steering

阶段一先不做 Micro-LED、不做 MQW、不做偶极子，只做平面波超表面：

```text
LCP, lambda = 450 nm, theta_in = 0 deg -> RCP, theta_out = +15 deg
```

同时要求：

```text
RCP_in -> 非目标衍射级 / 非目标角度
```

这一阶段借鉴 Compounding Fig. 4 的圆偏振 gradient metasurface 逻辑：LCP 入射时，几何相位和材料诱导相位共同形成目标相位梯度；RCP 入射时，两者破坏目标相位轮廓，导致非对称行为。

### 目标波长与偏转角

设定：

- lambda = 450 nm
- theta = 15 deg

光栅方程：

```text
sin(theta) = lambda / Lambda
Lambda = 450 nm / sin(15 deg) ~= 1.74 um
```

这里的 Lambda 是超分子 supercell 的整体周期。

### 原子数不先锁死 8 个

建议比较 N = 4, 6, 8：

| 原子数 N | 单元间距 p = Lambda / N | 相位步进 | 判断 |
| --- | --- | --- | --- |
| 4 | ~435 nm | 90 deg | 耦合弱、加工容易，但相位采样粗 |
| 6 | ~290 nm | 60 deg | 折中 |
| 8 | ~217 nm | 45 deg | 与 Compounding 逻辑最接近，但蓝光下耦合和加工压力最大 |

Compounding 使用八原子是因为它要构造 gradient metasurface，相邻 atoms 需要近似等振幅和固定相位差 Delta phi。但蓝光系统不一定必须固定为 8 个；如果 N = 4 或 N = 6 性能足够，反而可以形成低复杂度 few-atom meta-molecule 的亮点。

## 四、材料和结构选择

### 材料

优先材料：

- TiO2

理由：

- 蓝光透明；
- 折射率较高；
- 工艺相对成熟；
- 与 Gao 2021 的 TiO2 nanobrick 有传承关系。

第二选择：

- GaN

理由：

- 与 InGaN/GaN LED 工艺兼容；
- Taguchi 2026 已使用 GaN metasurface，并强调其与 InGaN LED 工艺体系兼容。

### 厚度

初始扫描：

```text
H = 250, 300, 350, 400, 450 nm
```

第一版建议从：

```text
H = 350 nm
```

开始。

判断标准：

- eta_{RCP<-LCP}^{+1} 是否高；
- eta_wrong_orders 是否低。

### 结构库

不要直接做完全自由拓扑。第一阶段采用多形状参数化 meta-atoms。

主力结构：

- 矩形纳米鳍；
- 椭圆柱；
- 双矩形组合。

扩展结构：

- 椭圆孔；
- C 型孔；
- L 型孔；
- split-ring。

建议三步走：

```text
矩形鳍 baseline -> 三形状库 -> 七形状库
```

不要一开始把七类都混在一起，否则数据空间会过大，优化难度上升。

## 五、机器学习路线

### 输入

使用完整 supercell 的结构图像，而不是只输入参数。

示例：

- 256 x 64；
- 或根据 N = 4, 6, 8 分别生成统一尺度的 supercell mask。

输入通道：

- 二值 mask：TiO2 / air；
- 可选 signed distance map；
- 可选形状类别 mask。

### 模型

前向代理模型：

```text
DenseNet-BC-small
```

理由：DenseNet 通过密集连接让每一层接收前面所有层的特征图，有利于信息流和梯度传播，并通过特征复用提升参数效率，适合结构图像到光学响应的回归问题。

### 输出标签

DenseNet 不只预测一个效率，而是预测多目标：

- eta_{R<-L}^{+1}
- eta_{L<-L}^{0}
- eta_{R<-R}^{+1}
- eta_{L<-R}^{+1}
- eta_wrong_orders
- A
- ER_spin

其中：

```text
ER_spin = 10 log10( eta_{R<-L}^{+1} / (eta_target_leakage_from_RCP + epsilon) )
```

### 优化方式

使用：

```text
DenseNet ensemble + active learning + NSGA-II / Bayesian optimization
```

流程：

1. 随机生成 3000-5000 个 supercell；
2. RCWA 计算偏振分辨衍射效率；
3. 训练 5 个 DenseNet ensemble；
4. 在大规模候选结构中预测；
5. 按照 `S = mu + kappa sigma` 选择高性能且高不确定度结构；
6. 重新 RCWA 标注；
7. 迭代 3-5 轮；
8. Top 50-100 个结构用 FDTD/FEM 验证。

## 六、阶段一评价指标

核心指标：

```text
eta_{R<-L}^{+1} = P(RCP, +15 deg | LCP_in)
```

opposite-spin 泄漏：

```text
eta_leak = P(target channel | RCP_in)
```

方向选择性：

```text
D_theta = P(+15 deg) / P(all transmitted angles)
```

目标方向圆偏振度：

```text
DCP_{+15 deg} = (I_R(+15 deg) - I_L(+15 deg)) / (I_R(+15 deg) + I_L(+15 deg))
```

非偏振等效输出：

```text
I_out_unpol = 1/2 I_out_LCP + 1/2 I_out_RCP
```

## 七、阶段二：Micro-LED 迁移

目标：

> Micro-LED 非偏振 MQW 发光 -> 目标方向高 RCP 纯度输出

目标仍然是 +15 deg，而不是全空间 CP。

### 是否一开始加 DBR

不建议一开始就加。

推荐三步：

#### Step 2.1：裸 Micro-LED + 单层超表面

不加 Al 光栅，不加 DBR。

目的：验证单层超表面极简方案是否可行。

仿真：

- MQW 中放置 x/y 偶极子；
- 结果非相干相加；
- 统计远场 RCP/LCP；
- 看 +15 deg 的 DCP 和 cone efficiency。

Taguchi 2026 也采用 x/y 偶极子非相干相加来模拟 InGaN QW 的非偏振发射，这一点可以直接作为方法参考。

#### Step 2.2：如果裸器件效果差，再加 DBR/RCLED

原因：LED 发光角度太宽，metasurface 只在有限角度范围内有效，导致全角度平均 CP 或方向性性能下降。Taguchi 2026 中，普通 LED + metasurface 的全角度平均 P_CP_total 很低，引入 RCLED cavity 后提升到约 0.6。

#### Step 2.3：和师兄路线对比

对比对象：

- Gao 2021：Al 光栅 + TiO2 QWP；
- 裸 Micro-LED + 本课题单层 spin-selective metasurface；
- RCLED/DBR + 本课题单层 spin-selective metasurface。

## 八、和已有文献的关系

| 文献 | 已有内容 | 对本课题的意义 | 必须避开的重复 |
| --- | --- | --- | --- |
| Gao 2021，组内师兄工作 | Al 光栅起偏 + TiO2 QWP + GaN Micro-LED CP emission | 组内基础 | 不能再只做 Micro-LED 圆偏振发光 |
| Taguchi 2026 | 单层 GaN metasurface 从非偏振 InGaN LED 中选择 CP 分量 | 支撑单层方案 | 不能只做垂直方向 CP 输出 |
| Compounding | 弱耦合 meta-molecule，800 nm，CP beam steering | 支撑 meta-molecule + spin-selective beam steering | 不能直接照搬金属结构 / CPPN + CC |
| DenseNet | 图像特征复用和高效训练 | 支撑结构图像代理模型 | 需要结合物理标签和主动学习 |

## 九、最终论文主线建议

### 第一篇 / 第一阶段标题

中文：

> 基于 DenseNet 主动学习的自旋选择性 TiO2 超分子超表面蓝光定向偏转

英文：

> DenseNet-assisted inverse design of spin-selective TiO2 meta-molecule metasurfaces for blue-light beam steering

### 第二篇 / 第二阶段标题

中文：

> 基于逆向设计超分子超表面的 Micro-LED 自旋选择性圆偏振定向出光

英文：

> Spin-selective directional circularly polarized emission from Micro-LEDs using inverse-designed meta-molecule metasurfaces

## 十、近期执行清单

### 立即做

固定：

- lambda = 450 nm
- theta = 15 deg
- Lambda = 1.74 um

比较：

- N = 4, 6, 8

材料先用：

- TiO2 / air；
- 或 TiO2 / SiO2。

厚度扫描：

- H = 250-450 nm

先做矩形纳米鳍 baseline。

### 第二步

- 加入椭圆柱和双矩形组合；
- 生成完整 supercell 图像；
- RCWA 计算：
  - LCP -> RCP, +15 deg；
  - RCP -> 所有衍射级；
- 训练 DenseNet-BC-small。

### 第三步

- 主动学习；
- Top 结构 FDTD/FEM 验证；
- 加入非偏振等效输出：

```text
I_unpol = 1/2 I_LCP + 1/2 I_RCP
```

- 再进入 Micro-LED 偶极子阶段。

## 最终一句话

先用平面波证明单层多形状 meta-molecule 超表面能够实现 LCP -> RCP, +15 deg，并将 RCP 重分配到非目标通道；再将该机制迁移到 Micro-LED，面向非偏振 MQW 发光实现目标方向上的高圆偏振选择性和方向选择性出光。

这条路线既继承了组内 Gao 2021 的 Micro-LED CP emission 基础，又吸收了 Taguchi 2026 的单层 CP-selective metasurface 思路，还通过 Compounding 的 meta-molecule beam steering 和 DenseNet 主动学习形成自己的创新闭环。
