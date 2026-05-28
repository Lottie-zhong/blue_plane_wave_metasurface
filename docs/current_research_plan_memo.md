# 当前课题最新方案备忘录

## 一、课题总定位

当前课题主线更新为：

> APCD-inspired spin-selective directional metagrating

旧路线是：

```text
450 nm TiO2 meta-atom gradient metasurface
N = 4 / 6 / 8 individual meta-atoms per supercell
rectangular nanofin baseline -> ellipse / dual-rectangle / multi-shape library
DenseNet-assisted optimization for LCP -> RCP, +15 deg
```

新路线改为：

```text
APCD-inspired dimer-supercell metagrating
```

核心目标仍然是自旋选择性圆偏振定向出光，但基本结构单元从“单个 meta-atom”改为“APCD dimer meta-molecule”。

## 二、核心物理概念

1. 单个 APCD dimer 是基本的 polarization-selective meta-molecule。
2. 每个 APCD dimer 由两个 birefringent nanopillars 组成。
3. Dimer 负责偏振选择 / 转换：

```text
LCP_in -> RCP_out
RCP_in -> suppressed / rejected from the target output channel
```

4. 多个 APCD dimers 组成一个 phase-gradient supercell。
5. Phase-gradient supercell 负责 beam steering：

```text
LCP_in -> RCP_out, +15 deg
```

因此，新路线的物理分工是：

```text
single APCD dimer: spin-selective polarization conversion
dimer supercell: phase gradient and +15 deg beam steering
```

## 三、重要记号更新

后续统一使用：

```text
K = number of APCD dimers per supercell
```

不要再用 N 表示 individual nanopillars 的数量。

总 nanopillars 数量为：

```text
total nanopillars per supercell = 2K
```

旧的 N=4/6/8 meta-atoms 表述只作为历史记录，不再作为新方案的主记号。

## 四、Stage 0 / Stage 1 目标

阶段目标：

```text
lambda = 633 nm
theta_out = +15 deg
Lambda = lambda / sin(15 deg) ~= 2.45 um
```

这里的 Lambda 是 dimer-supercell 总周期。

### 先比较 K = 6 和 K = 7

| K | Dimer pitch | Phase step | Total nanopillars | 判断 |
| --- | --- | --- | --- | --- |
| 6 | ~408 nm | 60 deg | 12 | lower inter-dimer coupling risk |
| 7 | ~349 nm | ~51.4 deg | 14 | close to APCD paper's 340 nm unit period |
| 8 | ~306 nm | 45 deg | 16 | later comparison only; higher inter-dimer coupling risk |

K = 8 不作为第一主路线，只保留为后续对比。

K = 7 的理由不是“奇数有特殊物理”。K = 7 只是一个几何匹配选项，因为：

```text
633 nm / sin(15 deg) ~= 2.45 um
2.45 um / 7 ~= 349 nm
```

这接近 APCD paper 中约 340 nm 的 unit period。

## 五、材料路线

### Stage 1A：c-Si / Al2O3 at 633 nm

目的：

```text
reproduce APCD-like dimer behavior
```

优先做单个 dimer 的偏振选择 / 转换验证，再做 K = 6 和 K = 7 dimer supercell。

### Stage 1B：TiO2 / SiO2 或 TiO2 / sapphire at 633 nm

目的：

```text
check whether the APCD-inspired mechanism can be migrated toward blue-light-compatible materials
```

这一阶段仍然在 633 nm 做机制迁移，不急着直接回到 450 nm。

### Stage 2：TiO2 或 GaN at 450 nm

目的：

```text
scale the verified dimer-metagrating mechanism back to blue Micro-LED wavelengths
```

### Stage 3：Micro-LED migration

目标：

```text
unpolarized MQW emission -> high-purity RCP output in the +15 deg target direction
```

## 六、机器学习路线更新

近期不训练 DenseNet。

近期不训练 cVAE。

### DenseNet 的定位

DenseNet 不是 inverse design 本身。DenseNet 后续只作为 forward surrogate：

```text
full dimer-supercell mask -> polarization-resolved diffraction matrix S_m^{q <- p}
```

真正的 inverse design 后续应定义为：

```text
DenseNet forward prediction
+ BO / NSGA-II / active learning search
+ RCWA / FDTD validation
```

### cVAE 的定位

cVAE 现阶段不用。

cVAE 只有在积累足够 labeled data 后，才可作为候选结构生成器：

```text
target response -> possible dimer-supercell candidates
```

之后仍然需要：

```text
DenseNet filter candidates
RCWA / FDTD validate candidates
```

## 七、未来两周冻结方向

未来两周只做 physics validation：

1. Single APCD dimer at 633 nm。
2. K = 6 和 K = 7 dimer supercells at 633 nm。
3. TiO2 material feasibility at 633 nm。

明确不做：

- large dataset generation；
- DenseNet training；
- cVAE training；
- 3000-5000 structure sweep。

## 八、近期执行清单

### Step 0：单个 APCD dimer

目标：

```text
633 nm, c-Si / Al2O3
LCP_in -> RCP_out
RCP_in -> suppressed / rejected from target-like channel
```

输出：

- LCP/RCP 输入下的 transmitted polarization components；
- conversion efficiency；
- rejection / leakage metric；
- dimer parameter sanity range。

### Step 1：K = 6 / K = 7 dimer-supercell

固定：

```text
lambda = 633 nm
theta_out = +15 deg
Lambda ~= 2.45 um
```

比较：

- K = 6：dimer pitch ~= 408 nm；
- K = 7：dimer pitch ~= 349 nm。

输出：

- eta_{RCP <- LCP}^{+1}
- target leakage from RCP input
- opposite-spin redistribution channel
- spin extinction ratio
- all-order polarization-resolved diffraction spectrum

### Step 2：TiO2 material feasibility at 633 nm

目标：

```text
same APCD-inspired dimer mechanism
but replace material stack with TiO2 / SiO2 or TiO2 / sapphire
```

判断：

- 是否仍有可用 dimer-level polarization selectivity；
- K = 6 / K = 7 metagrating 是否仍能保持目标通道效率；
- 如果 633 nm 可行，再考虑 scale to 450 nm。

## 九、旧结果的定位

旧的 450 nm TiO2 PB nanofin metagrating 结果不删除，但定位变为历史 baseline / 方法验证：

- 它证明了本项目的 Lumerical 自动化链路、grating order 提取、RCP/LCP handedness spectrum、spin extinction ratio 汇总流程是可用的；
- 它不再是当前论文主路线；
- 后续可以复用其脚本思想，但几何对象要从 individual nanofin supercell 切换为 APCD dimer-supercell。

## 十、最终一句话

当前主线是：

> 先在 633 nm 复现并验证 APCD-inspired dimer 的自旋选择性偏振转换，再用 K = 6 / K = 7 dimer-supercell 构建 +15 deg phase-gradient metagrating；随后测试 TiO2 等蓝光兼容材料的机制迁移，最后再回到 450 nm Micro-LED 定向圆偏振出光。
