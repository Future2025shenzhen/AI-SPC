# GitHub 投射器实现参考与本轮优化

2026-10-26：通过 GitHub 搜索后，实际拉取并阅读以下仓库。仅借鉴交互与教学呈现思路；未复制其代码、图片或字体。

| 项目与阅读版本 | 借鉴点 | 本程序的实现 |
|---|---|---|
| [jchen208208/Improved-Catapult_Simulation-Website](https://github.com/jchen208208/Improved-Catapult_Simulation-Website/tree/ad345384f6bd14778ef09cd765fd6b2262ed9f1f) | 拖动上弦、状态反馈、重力与二次阻力说明；阅读 README、sim.js、physics.js、hud.js | 保留五因子控制，增加物理时间、臂角、球速、离地高度。该项目是配重投石机，其配重能量公式不适用于本弹力绳装置。 |
| [thred/xkcd-time-catapult](https://github.com/thred/xkcd-time-catapult/tree/afbb1f7ab2e00486ceff85fb74338cda37d6bb5b) | Main.js 播放速度控制、Catapult.js 速度显示 | 增加 0.25× / 0.5× / 1× / 2×、暂停、继续；播放不改变积分结果。 |
| [unirone777/catapult-simulation](https://github.com/unirone777/catapult-simulation/tree/d597b2f8b8d2096d09036ed12a0a3d1a9b3ecdfb) | index.html 分阶段动画、轨迹逐渐绘制、发射记录 | 增加机构回转／飞行／首次落地状态；只画已走过的轨迹。未采用其正弦插值示意弹道，继续使用本程序的 RK4 物理路径。 |

本轮新增回放与落地后的时间轴拖动；回放使用原发射的积分数据和目标快照，不重新抽样、不增加记录、不改变参数。发射与回放期间锁定参数和目标。两种结构版本同步提供上述改进，机构几何和物理参数保持原定义。

1× 表示整发 1.35 秒的教学播放基准，不保证等于真实时间倍率；面板“物理时间”取自积分时间。更改播放速度只改变画面进度。回放中的参数卡显示原发射设置；返回参数调节时恢复当前设置。首次落地作为 DOE 响应，不模拟反弹与滚动。

验证包含：独立 SciPy 射程比对、SVG 共轴与 D 刻度、两版 25 次 CCF 与拟合、实际鼠标拖动、暂停继续、速度切换、回放与时间轴不改变随机流／记录、390px 移动端布局。
