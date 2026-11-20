# 小行星 V 波段视星等：H–G₁₂ + JPL Horizons

本包沿用第一周的 `sbpy.photometry.HG12`（Muinonen 2010），增加三种可复用入口：输入观测几何、输入三维位置、在线查询 JPL Horizons。默认在线观测者为地球质心；开普勒模型保留为演示来源。

## 安装

在项目根目录执行：

```bash
python -m pip install -e .
python -m pip install -e '.[plot]'  # 绘制示例图
```

需要 Python ≥3.10。如有多个 Python，请用与依赖安装相同的解释器。核心离线接口不访问网络；`source="jpl"` 需要连接 NASA JPL。astroquery 使用本地查询缓存，重复相同查询可复用缓存；大量连续时刻宜批量查询或使用 SPK 扩展。

## 在其他项目中调用

```python
from asteroid_brightness import (
    magnitude_from_geometry, magnitude_from_positions, magnitude_at, OrbitParams,
)

# 距离 AU、角度度；标量结果为 float。
v = magnitude_from_geometry(H=20, G12=0.5, r_au=2, delta_au=1, alpha_deg=10)

# 三个位置必须处于相同参考系、原点和历元；(..., 3) 数组可批量计算。
v_sat = magnitude_from_positions(
    asteroid_pos_au=[2, 0, 0], observer_pos_au=[1, 0, 0],
    H=20, G12=0.5, sun_pos_au=[0, 0, 0],
)

# 433 Eros；UTC ISO 8601；返回 BrightnessResult。
eros = magnitude_at(433, "2026-11-20T00:00:00Z", H=10.4, G12=0.5)
print(eros.v_mag, eros.r_au, eros.delta_au, eros.alpha_deg)

# 多时刻返回 BrightnessResult 列表，顺序与输入相同。
series = magnitude_at(433, ["2026-11-20T00:00:00Z", "2026-11-22T00:00:00Z"], 10.4, 0.5)

# 无网络的第一周共面开普勒示例；此时 asteroid_id 仅作标签。
orbit = OrbitParams(2.2, 0.15, 20, "2026-01-01T00:00:00Z")
demo = magnitude_at("demo", "2026-11-20T00:00:00Z", 20, 0.5,
                    source="kepler", asteroid_orbit=orbit)
```

`BrightnessResult` 含 `v_mag, r_au, delta_au, alpha_deg, time_utc`。JPL 模式另含 `jpl_v_mag, jpl_h, jpl_g` 供比较。JPL 的 `G` 是 H–G 模型斜率参数，**不是**本包的 `G12`；`v_mag` 始终由传入的 `H, G12` 重算，不复制 JPL 的预测 V 值。JPL 观测者表包含其标准光行时处理；离线位置接口则按给定位置作瞬时几何计算。

## Eros 真实案例

```bash
python examples/eros_jpl.py
```

脚本查询 2026-11-01 至 2026-12-01 每两天共 16 个时刻，生成 `asteroid_brightness/outputs/data/eros_jpl.csv` 和 `asteroid_brightness/outputs/figures/eros_jpl_comparison.png`。示例使用 `H=10.4, G12=0.5`；JPL 同期提供 `H=10.4, G=0.46` 的 H–G 参考值。两条曲线的差异主要来自相位函数不同，不能把 `G` 直接当作 `G12`。

## 可选 SPK / SPICE 扩展

```bash
python -m pip install -e '.[spice]'
```

`asteroid_brightness.ephemeris_spice.download_asteroid_spk(id, start_utc, stop_utc, cache_dir)` 从 Horizons 下载一次小行星 BSP，按目标和时间窗缓存，返回 `(文件路径, SPK ID)`。`positions_from_spk(...)` 用 spiceypy 本地读取小行星、观测者和太阳相对于太阳系质心的 J2000 三维 AU 向量，随后可传给 `magnitude_from_positions`。调用者须提供覆盖同一时段的 NAIF 行星 SPK 和闰秒内核。该扩展未完成完整内核集的数值验收；高频仿真前应与同一时刻 Horizons 观测者表交叉核对。

## 第一周演示与测试

```bash
python main.py --time 2026-11-26T00:00:00Z
python main.py --start 2026-11-01T00:00:00Z --end 2026-12-01T00:00:00Z --step-days 2 --plot
python -m unittest discover -s asteroid_brightness/tests -v
```

第一周输出保存在 `asteroid_brightness/outputs`。相位角定义为小行星指向太阳与指向观测者的夹角；零相位时 `r=Δ=1 AU` 得 `V≈H`。第一周相位曲线仅绘制 0°–120°。本项目不含自转、复杂形状、仪器噪声或定轨算法。

参考仓库 `inner_asteroid` 未发现许可证文件，因此只参考了星历下载与位置计算思路，没有复制其源码。接口设计参考 [astroquery Horizons 文档](https://astroquery.readthedocs.io/en/latest/jplhorizons/jplhorizons.html) 和 [JPL Horizons 手册](https://ssd.jpl.nasa.gov/horizons/manual.html)。
