"""ComfyUI Browser插件主入口"""
import os
from aiohttp import web
import server

from .config import BROWSER_PATH, get_collections_path, get_sources_path, get_outputs_path
from .routes import files, sources, collections, config, downloads

# 创建应用
browser_app = web.Application()

# 注册路由
browser_app.add_routes([
    # Files
    web.get("/files", files.api_get_files),
    web.delete("/files", files.api_delete_file),
    web.put("/files", files.api_update_file),
    web.get("/files/view", files.api_view_file),

    # Collections
    web.post("/collections", collections.api_add_to_collections),
    web.post("/collections/workflows", collections.api_create_new_workflow),
    web.post("/collections/sync", collections.api_sync_my_collections),

    # Sources
    web.get("/sources", sources.api_get_sources),
    web.post("/sources", sources.api_create_source),
    web.delete("/sources/{name}", sources.api_delete_source),
    web.post("/sources/sync/{name}", sources.api_sync_source),
    web.get("/sources/all", sources.api_get_all_sources),

    # Config
    web.get("/config", config.api_get_browser_config),
    web.put("/config", config.api_update_browser_config),

    # Downloads
    web.post("/downloads", downloads.api_create_new_download),
    web.get("/downloads", downloads.api_list_downloads),
    web.get("/downloads/{uuid}", downloads.api_show_download),

    # Static files
    web.static("/web", os.path.join(str(BROWSER_PATH), 'web-ui/release')),
    web.static("/s/outputs", get_outputs_path()),
    web.static("/s/collections", get_collections_path()),
    web.static("/s/sources", get_sources_path()),
])

# 注册到ComfyUI Server
server.PromptServer.instance.app.add_subapp("/browser/", browser_app)

# ComfyUI节点配置
WEB_DIRECTORY = "web-ui"
NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}
