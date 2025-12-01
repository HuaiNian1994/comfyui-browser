# ComfyUI 浏览器
本项目是为comfyUI设计的插件,只有前端界面，没有为画布自定义节点。

## 功能

- 浏览和管理 ComfyUI 输出文件
- 添加工作流到收藏夹，方便管理和调用
- 可以通过 Git 来远程同步收藏夹
- 订阅工作流仓库，方便抄作业
- 通过关键词搜索工作流


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


