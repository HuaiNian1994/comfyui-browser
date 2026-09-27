# ComfyUI 浏览器
本项目是为comfyUI设计的插件,只有前端界面，没有为画布自定义节点。

## 功能

- 浏览和管理 ComfyUI 输出文件
- 添加工作流到收藏夹，方便管理和调用
- 可以通过 Git 来远程同步收藏夹
- 订阅工作流仓库，方便抄作业
- 通过关键词搜索工作流


## 图片关键属性

图片预览侧边栏按输出分支和生成阶段显示提示词、模型资源、采样参数、尺寸、控制条件及放大与修复参数。展开“节点来源”可核对属性对应的执行图节点和输入字段；运行结果未保存时显示未知原因。

支持属性、节点端口和适配版本见 [图片属性与节点支持清单](docs/METADATA_SUPPORT.md)。升级解析规则后，浏览目录或打开图片会自动补齐历史元数据。

新生成图片会自动记录任务总耗时、实际采样耗时和平均采样速度，在预览顶部显示。PNG/APNG/WebP 可携带独立计时元数据，复制或收藏后仍可读取。计时口径、覆盖限制及维护方式见 [图片生成计时](docs/GENERATION_TIMING.md)，本机真实生成结果见 [验收报告](docs/TIMING_ACCEPTANCE.md)。

维护检查：`python scripts/metadata_support.py --check`；后端测试：`python -m unittest discover -s tests -v`。

## 开发

- 前置需求
  - 安装[Node](https://nodejs.org/en/download/current)

- 使用的框架

  - 前端: vite+vue3+ts+element plus+pnpm
  - 后端: [aiohttp](https://docs.aiohttp.org/)(和 ComfyUI 一样)

- 目录介绍

```
├── __init__.py  (后端服务)
├── web-ui       (ComfyUI 加载的前端代码)
    ├── build    (Vite 的生成文件)
    └── index.js (和 ComfyUI 交互的前端代码)
```

- 开发和调试

直接运行dev.bat
