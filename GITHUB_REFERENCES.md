# GitHub 投射器实现参考与本轮优化

2026-10-26：通过 GitHub 搜索后，实际拉取并阅读以下仓库。仅借鉴交互与教学呈现思路；未复制其代码、图片或字体。

| 项目与阅读版本 | 借鉴点 | 本程序的实现 |
|---|---|---|
| [jchen208208/Improved-Catapult_Simulation-Website](https://github.com/jchen208208/Improved-Catapult_Simulation-Website/tree/ad345384f6bd14778ef09cd765fd6b2262ed9f1f) | 拖动上弦、状态反馈、重力与二次阻力说明；阅读 README、sim.js、physics.js、hud.js | 保留五因子控制，增加物理时间、臂角、球速、离地高度。该项目是配重投石机，其配重能量公式不适用于本弹力绳装置。 |
| [thred/xkcd-time-catapult](https://github.com/thred/xkcd-time-catapult/tree/afbb1f7ab2e00486ceff85fb74338cda37d6bb5b) | Main.js 播放速度控制、Catapult.js 速度显示 | 增加 0.25× / 0.5× / 1× / 2×、暂停、继续；播放不改变积分结果。 |
| [unirone777/catapult-simulation](https://github.com/unirone777/catapult-simulation/tree/d597b2f8b8d2096d09036ed12a0a3d1a9b3ecdfb) | index.html 分阶段动画、轨迹逐渐绘制、发射记录 | 增加机构回转／飞行／首次落地状态；只画已走过的轨迹。未采用其正弦插值示意弹道，继续使用本程序的 RK4 物理路径。 |


| [noriskworld/digital-catapult](https://github.com/noriskworld/digital-catapult/tree/24b5ce848f03dd9ed89bcc80e3e4bebfbd9ec81d) | README、animation.js、physics.js 的公共坐标、同尺度全景、自适应视野、DOE 响应与显示一致 | 本轮全景使用单一 px/m 比例，画出同一机构、球及地面标尺；局部 SVG 保持独立放大。保留本装置 D 沿支架、E 沿臂的定义，不采用该项目不同的因子含义或其集中阻力近似。 |
| [jjesperlund/catapult-simulation](https://github.com/jjesperlund/catapult-simulation/tree/37b880c0466dcb2a51e0b1d4f0c925b6448fb04a) | README、loadObjects.js、RenderFunctions.js 的机架层次、材质、投影及落点环 | 使用原创 SVG 的双侧板、金属轴件、槽孔、软阴影，落点以环标识。保持侧视交互，不引入其外部模型、纹理、三维库或按帧增量的机械运动。 |
| [SuyamaCorporation/catapult-projectile-physics-sim](https://github.com/SuyamaCorporation/catapult-projectile-physics-sim/tree/6d77d107ca9cb3150bf7c541f76196b2764eeda4) | README、index.html 的多弹道对比、动态读数 | 新增最近五发实测轨迹叠加，用不同颜色与序号区分；保留本程序 RK4 求解，不把出射速度作为任意输入。 |

| [psandis/castle3d](https://github.com/psandis/castle3d/tree/18350099343768121fc64f91ab2a1ea035e60ecd) | README、src/controls.js、src/main.js 的相机控制、对象支点与连续场景呈现 | 由场景与相机控制得到启发，独立实现 SVG 主画面的平滑展开镜头；球从杯中到落地始终在同一个世界坐标系。该项目提供手动三维相机，不声称它实现了这里的自动跟随；未采用其游戏抛物线、模型、贴图或声音。 |

本项目保留回放与落地后的时间轴拖动；回放使用原发射的积分数据和目标快照，不重新抽样、不增加记录、不改变参数。发射与回放期间锁定参数和目标。两种结构版本同步提供上述改进，机构几何和物理参数保持原定义。

提供两种播放模式：教学模式分别慢放回转和飞行（回转至少 500 ms、飞行至少 900 ms）；物理时间模式按积分时间播放。四档倍率作用于所选模式。面板“物理时间”始终取自积分数据，显示射程不随播放模式或倍率改变。回放中的参数卡显示原发射设置；返回参数调节时恢复当前设置。首次落地作为 DOE 响应，不模拟反弹与滚动。

验证包含：独立 SciPy 射程比对、SVG 共轴与 D 刻度、两版 25 次 CCF 与拟合、实际鼠标拖动、暂停继续、速度切换、回放与时间轴不改变随机流／记录、390px 移动端布局。


## 结构与发射重绘

- 提升机构近景占比，重绘机架双侧板、底座、轴承、限位杆、D 槽及底部零点、球杯、E 绳挂点与导轨。
- A、B 仍共用 O；两个版本分别保留 D 随 B 绕 O 和 D 固定的定义。
- 球心对准 C 的物理位置；离杯前在杯中运动，离杯瞬间切换至同一积分轨迹，首次落地后保持 B。
- B 的调节徽标用引线移到臂旁，避免其点击区域挡住黄色臂。真实限位杆仍在 O 转动。
- 落地后直接拉臂从画面中的 B 开始，不从原 A 跳动；“重新上弦”可恢复当前设定姿态，不产生一发数据。
- 动画每帧更新部件变换，不重复创建整棵 SVG；参数改变时才重建静态结构。
- 三目标、±15 cm、公差命中、随机流、重复验证及 DOE 分析维持一致。

这是实际阅读的七个项目的选择性综合，不声称穷尽 GitHub 的所有投射器项目；配重投石机、弹弓及本装置的力学结构不同，只吸收适用的设计。细杆及球在全景中作可见性放大，位置和横纵距离采用同一比例尺。近景外壳为带材质层次的侧视示意图，不是加工工程图。


## 连续主画面与结构透视

球的局部 SVG 位置与 RK4 弹道共用同一世界坐标，离杯时以 `x = Oₓ + r cosB + x飞行`、`y = Oᵧ + H − y飞行` 换算，不改变球的坐标来配合镜头。主画面从近景以 smoothstep 平滑展开，保持横纵同尺度；镜头只调整 viewBox。地面、投射器底座、目标、公差带和标尺均放在同一坐标系。放大的球是便于观察的标记，非球径标尺。

结构透视只改变机架外壳的透明度。全程跟随、结构透视和重新上弦不消耗随机数、不增加记录、不修改五因子或动力学模型。新增浏览器测试扫描完整飞行采样，校验离杯位置无跳跃、球保持在视野内、变焦连续且首次落点正确。


## SigmaZone 原站对照与落地式优化

本轮再次访问 https://www.sigmazone.com/catapult/ 并使用原页面指针操作限位、拉臂和松手发射，观察离杯与落地事件。吸收其装置与控制分区、底座层次、角度限位和沿部件调节的呈现；继续使用独立绘制的图形和本程序公开的教学模型，未嵌入原站商标、图片或代码。

本轮保留落地式结构，按用户最新要求缩短并加高底座、降低共轴支点；量角器以共同 O 为原点绘制。两个按钮移到图像左上方，机身点击改为只重新上弦。两种结构仍分别提供，模型离地高度同步改变，详见 PHYSICS_NOTES.md。
