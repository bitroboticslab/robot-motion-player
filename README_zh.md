<div align="center">
<!--   <img src="assets/banner.png" alt="Robot Motion Player" width="100%"/> -->

  # 机器人运动播放器

  **可视化 • 调试 • 验证机器人运动数据**

  [![CI Status][ci-badge]][ci-url]
  [![License][license-badge]](LICENSE)
  [![Python][python-badge]](https://www.python.org/)
  [![GitHub Stars][star-badge]][star-url]
  [![GitHub Forks][fork-badge]][fork-url]
  [![Contributors][contrib-badge]][contrib-url]

  [English](README.md) | [中文](README_zh.md)
</div>

---

## 概述
Robot Motion Player是一款独立、跨平台的Python工具，用于机器人运动数据集的可视化、编辑和质量评估，支持AMP格式数据和全身轨迹优化结果。

**核心能力：**
- 🎬 **播放**：优先基于MuJoCo的实时运动回放
- 🎚️ **IK调试**：6D末端执行器位姿调整
- 📊 **指标计算**：对齐AMP标准的质量评估
- ✏️ **编辑**：关键帧安全的轨迹编辑
- 🔄 **格式转换**：URDF/XML格式互相转换
- 📤 **导出**：GIF/视频输出

**使用场景：**
- AMP locomotion学习流水线（GMR → rsl-rl-ex → 训练）
- 轨迹优化可视化和调试
- 昂贵GPU训练前的运动数据质量控制
- 机器人运动算法开发

---

## 功能演示
<table>
<tr>
<td width="50%" align="center"><b>播放 + 控制</b></td>
<td width="50%" align="center"><b>IK调试</b></td>
</tr>
<tr>
<!-- <td><img src="assets/demo/playback.gif" width="100%"></td> -->
<!-- <td><img src="assets/demo/ik_tuning.gif" width="100%"></td> -->
</tr>
<tr>
<td align="center"><b>指标报告</b></td>
<td align="center"><b>GUI工作台</b></td>
</tr>
<tr>
<!-- <td><img src="assets/demo/metrics.gif" width="100%"></td> -->
<!-- <td><img src="assets/demo/audit.gif" width="100%"></td> -->
</tr>
</table>

---

## 功能列表
| 模块 | 功能 | 状态 |
|--------|----------|--------|
| 📽️ **播放** | 实时回放、键盘控制、帧标记 | ✅ |
| 🎚️ **IK调试** | 6D目标位姿、单位感知控制、基于雅可比计算 | ✅ |
| 📊 **指标计算** | AMP质量项、GMR损失对齐、JSON/CSV导出 | ✅ |
| ✏️ **编辑** | 帧/片段编辑、撤销/重做、跨帧传播 | ✅ |
| 🔄 **格式转换** | URDF↔XML、MuJoCo格式支持 | ✅ |
| 📤 **导出** | GIF、MP4、帧序列 | ✅ |
| 🖥️ **GUI** | 全功能工作台（播放/调试/指标/审计） | ✅ |

---

## 📦 安装方式
> PyPI版本正在审核上线中，当前推荐使用源码安装：

### 用户安装（直接使用）
```bash
git clone https://github.com/bitroboticslab/robot-motion-player.git
cd robot-motion-player
pip install ".[all]"
```

### 开发者安装（参与贡献）
```bash
git clone https://github.com/bitroboticslab/robot-motion-player.git
cd robot-motion-player
conda create -n rmp python=3.11 -y
conda activate rmp
conda install -c conda-forge pinocchio
pip install -e ".[all,dev]"
pre-commit install
```

### 脚本安装（Linux、macOS、Windows）
为了更顺畅的安装体验，提供了平台专用安装脚本：
```bash
# Linux
chmod +x scripts/setup_linux.sh
bash scripts/setup_linux.sh

# macOS
chmod +x scripts/setup_mac.sh
bash scripts/setup_mac.sh

# Windows
scripts\setup_windows.bat
```

### 手动源码安装（全平台通用）
```bash
git clone https://github.com/bitroboticslab/robot-motion-player.git
cd robot-motion-player
conda create -n rmp python=3.11 -y
conda activate rmp
# Windows用户推荐安装conda版pinocchio避免编译
conda install -c conda-forge pinocchio
pip install -e ".[all]"
```

---

## ⚡ 快速开始
### 使用示例数据体验
```bash
# 克隆仓库
git clone https://github.com/bitroboticslab/robot-motion-player.git
cd robot-motion-player

# 基础播放
motion_player play \
  --motion example/standard_dataset/run1_subject5_standard.pkl \
  --robot example/robots/booster_t1/T1_23dof.xml

# GUI模式
motion_player gui \
  --motion example/standard_dataset/run1_subject5_standard.pkl \
  --robot example/robots/booster_t1/T1_23dof.xml

# 生成质量报告
motion_player metrics \
  --motion example/standard_dataset/run1_subject5_standard.pkl \
  --output report.json
```

---

## 📖 文档
- [快速上手指南](docs/QUICKSTART_zh.md)
- [IK使用指南](docs/IK_USAGE.md)

- 📚 [详细中文快速上手指南](docs/QUICKSTART_zh.md)
---

## 生态集成
Robot Motion Player设计支持与以下项目集成：
| 项目 | 作用 |
|---------|------|
| [GMR](https://github.com/YanjieZe/GMR) | 人体到机器人运动重定向 |
| [rsl-rl-ex](https://github.com/Mr-tooth/rsl-rl-ex) | AMP数据集构建和训练 |
| [Pinocchio](https://github.com/stack-of-tasks/pinocchio) | IK后端（可选） |

---

## 引用
如果您在研究中使用了Robot Motion Player，请引用：
```bibtex
@software{rmp2026,
  author = {Lai, Junhang and contributors},
  title = {Robot Motion Player: A Visualiser and Editor for Robot Motion Data},
  howpublished = {https://github.com/bitroboticslab/robot-motion-player},
  year = {2026}
}
```

---

## 贡献
欢迎贡献代码！请查看贡献指南即将上线，欢迎提交Issue交流了解贡献指南。

---

## 许可
本项目采用Apache 2.0许可，详情见[LICENSE](LICENSE)文件。

---

## 致谢
本项目基于以下优秀开源项目构建：
- [Pinocchio](https://github.com/stack-of-tasks/pinocchio) — 刚体动力学计算
- [MuJoCo](https://github.com/google-deepmind/mujoco) — 物理仿真
- [GMR](https://github.com/YanjieZe/GMR) — 运动重定向

<!-- Links -->
[ci-badge]: https://github.com/bitroboticslab/robot-motion-player/actions/workflows/ci.yml/badge.svg
[ci-url]: https://github.com/bitroboticslab/robot-motion-player/actions/workflows/ci.yml
[star-badge]: https://img.shields.io/github/stars/bitroboticslab/robot-motion-player
[star-url]: https://github.com/bitroboticslab/robot-motion-player/stargazers
[fork-badge]: https://img.shields.io/github/forks/bitroboticslab/robot-motion-player
[fork-url]: https://github.com/bitroboticslab/robot-motion-player/network/members
[contrib-badge]: https://img.shields.io/github/contributors/bitroboticslab/robot-motion-player
[contrib-url]: https://github.com/bitroboticslab/robot-motion-player/graphs/contributors
[license-badge]: https://img.shields.io/badge/License-Apache%202.0-blue.svg
[python-badge]: https://img.shields.io/badge/Python-3.9%2B-blue
