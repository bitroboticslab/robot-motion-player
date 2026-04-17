# 快速上手（5 分钟）

本指南用于最快验证 `robot-motion-player` 可正常运行。

## 1）创建并激活环境

```bash
conda create -y -n rmp python=3.11 pip
conda activate rmp
pip install -e ".[dev,mujoco]"
pip install -e ".[dev,mujoco,gui]"
pip install -e ".[video]"
```

## 2）播放一个动作片段

```bash
motion_player play --motion path/to/clip.pkl --robot path/to/robot.xml

# 可选：启动双语控制面板（英文/中文）
motion_player play --motion path/to/clip.pkl --robot path/to/robot.xml --gui

# 可选：启动独立 GUI 工作台
motion_player gui --motion path/to/clip.pkl --robot path/to/robot.xml
```

`motion_player gui` 现在默认优先使用面板隔离进程模式。
若面板启动失败，运行时会打印告警并自动回退到 MuJoCo 键盘控制模式。

## 3）常用按键

- `Space`：播放/暂停
- `←/→`：上一帧/下一帧
- `Shift+←/→`：±10 帧
- `Ctrl+←/→`：±100 帧
- `1..9`：切换片段
- `[` / `]`：速度 -/+ 0.1x（限制在 `0.1x..4.0x`）
- `S`：保存编辑后片段
- `Q`：开关 HUD
- `Esc`：退出

启用 GUI（`play --gui` 或 `gui`）后，工作台提供分栏工具：
`Play`、`Tune`、`Metrics`、`Audit`、`Convert`、`Export`、`Audio`。
控制面板仍可覆盖全部键盘映射操作（`±1/10/100` 步进、循环/乒乓、
保存、HUD 开关、速度 ±、片段切换、退出）。
每个交互控件均支持悬停提示，可说明该操作的含义。
状态停靠区将运行监控、输出日志和进度显示合并在一起，便于快速查看播放状态。
Tune 分栏支持全姿态 IK 数值编辑（位置 + 朝向）、单位切换（`m / cm / mm`、`rad / deg`）
与步长微调按钮，便于精确调参。
Tune 工作流采用双层数据流：`Current Pose`（运行态只读）与 `Target Pose`（可编辑输入），
并提供 `Reference Frame`（`world` / 局部坐标）显式切换。
高分辨率屏幕可使用 GUI 顶部 `字号` 选择器（位于 `语言` 旁）调整显示大小；
若没有可用的 CJK 字体，界面会回退到可读的平台字体。
输出菜单提供 `清空` 操作，导出进度条按逐帧渲染进度更新。
当前 IK 说明请参考 [IK 使用说明](IK_USAGE.md)。

GUI 可视化质检命令（桌面会话）：

```bash
RMP_GUI_SNAPSHOT_OUT=/tmp/rmp-monitor-card.png \
RMP_GUI_LAYOUT_REPORT_OUT=/tmp/rmp-monitor-card-layout.json \
motion_player play --motion path/to/clip.pkl --robot path/to/robot.xml --gui
```

`/tmp/rmp-monitor-card-layout.json` 的期望字段：`"fits_all_lines": true`。

## 4）导出质量报告

```bash
motion_player metrics --motion path/to/clip.pkl --output report.json
motion_player metrics --motion path/to/clip.pkl --output report.csv
```

## 5）审查关节顺序

```bash
motion_player audit --motion path/to/clip.pkl --robot path/to/robot.xml --output joint_order.yaml
```

## 6）模型文件转换

```bash
# 支持的转换方向
motion_player convert --input path/to/robot.urdf --output path/to/robot.xml

# 当输入与输出都是 .xml 时按“无转换”路径处理
motion_player convert --input path/to/robot.xml --output path/to/robot.xml

# 安装外部后端后可执行 XML -> URDF（示例）
motion_player convert --input path/to/robot.xml --output path/to/robot.urdf
```

说明：
- `.urdf -> .xml`：支持
- `.xml -> .xml`：无转换并给出提示
- `.xml -> .urdf`：需外部后端（如 `mjcf2urdf`）或设置 `RMP_XML_TO_URDF_CMD`

## 7）导出回放文件

```bash
motion_player export \
  --motion path/to/clip.pkl \
  --robot path/to/robot.xml \
  --output /tmp/clip.gif \
  --fps 20
```

## 常见问题

- `mujoco package is required`：执行 `pip install -e ".[mujoco]"` 安装可选依赖。
- `Isaac backend is not available`：v0.1 请使用 `--backend mujoco`。
- `Motion path not found` / `Robot model path not found`：检查路径是否真实存在。
- 中文标签显示为 `???`：请安装 CJK 字体，并设置 `RMP_GUI_FONT=/absolute/path/to/font.ttf`。
- 若 GUI 启动出现 DearPyGui 字体范围错误，请升级到最新补丁版本，并确保 `RMP_GUI_FONT` 指向有效的 CJK 字体文件。
- 若 GUI 启动提示面板进程失败，说明当前已进入 viewer-only 回退模式，播放仍可继续。
