# ComfyUI 浏览器

查看和管理 ComfyUI 涉及的文件，并且添加收藏方便随时调用。

远程同步工作流到你的 Git 仓库，方便团队共享和版本管理。

还能订阅社区开放的工作流仓库，方便抄作业！

https://github.com/talesofai/comfyui-browser/assets/828837/803ce57a-1cf2-4e1c-be17-0efab401ef54

也可以参考B站的中文解说：
https://www.bilibili.com/video/BV1qc411m7Gp/

## 功能

- 浏览和管理你的 ComfyUI 输出文件
- 添加工作流到收藏夹，方便管理和调用
- 可以通过 Git 来远程同步收藏夹
- 订阅工作流仓库，方便抄作业
- 通过关键词搜索工作流


## 预览



## 安装方式

### ComfyUI Manager
安装[ComfyUI Manager](https://github.com/ltdrdata/ComfyUI-Manager)， 在 Install Custom Node 中搜索 `comfyui-browser` 来安装。

### 手动

下载这个仓库的代码放到 `ComfyUI/custom_nodes` 目录下，并重启 ComfyUI。

```bash
cd custom_nodes && git clone https://github.com/tzwm/comfyui-browser.git
```

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

  - 复制或者链接 `comfyui-browser` 到 `ComfyUI/custom_nodes/`
  - 启动服务端: `cd ComfyUI && python main.py --enable-cors-header`
  - 启动前端: `cd ComfyUI/custom_nodes/comfyui-browser/svelte && npm i && npm run dev`
  - 调试地址 `http://localhost:5173/?comfyUrl=http://localhost:8188`
    - `localhost:8188` 是 ComfyUI server 地址
    - `localhost:5173` 是 Vite dev server

- 备注

  - 请尽量在 Windows 上测试, 因为我只有 Linux 和 macOS
  - 在 ComfyUI 中可以按 'B' 键来打开/关闭 Browser



## 更新记录

详见：[ChangeLog](CHANGELOG.md)

## 感谢

- [ComfyUI](https://github.com/comfyanonymous/ComfyUI)
