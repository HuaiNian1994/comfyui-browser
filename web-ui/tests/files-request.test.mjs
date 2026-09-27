import test from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import vm from 'node:vm'
import ts from 'typescript'
import * as Vue from 'vue'
import dayjs from 'dayjs'

async function loadModule(path, bindings = {}) {
  const raw = await readFile(new URL(path, import.meta.url), 'utf8')
  const source = raw.includes('<script') ? raw.match(/<script lang="ts">([\s\S]*?)<\/script>/)[1] : raw
  const code = ts.transpileModule(source.replace(/^import[\s\S]*?from ['"][^'"]+['"];?\s*$/gm, ''), { compilerOptions: { target: ts.ScriptTarget.ES2020, module: ts.ModuleKind.CommonJS } }).outputText
  const context = vm.createContext({ exports: {}, console: { error() {} }, ...Vue, dayjs, Map, Set, URLSearchParams, AbortController, setTimeout, clearTimeout, ...bindings })
  vm.runInContext(code, context)
  return context.exports
}
const flush = async () => { await new Promise(resolve => setImmediate(resolve)); await Vue.nextTick() }
async function harness() {
  const requests = [], summaries = [], timers = new Map()
  let id = 0
  const utils = await loadModule('../src/utils/index.ts')
  const clock = { setTimeout(callback, delay) { timers.set(++id, { callback, delay }); return id }, clearTimeout(id) { timers.delete(id) } }
  const { DirectoryCoordinator } = await loadModule('../src/api/directory-coordinator.ts', {
    ...utils, ...clock,
    fetchFilesList(...args) { return new Promise((resolve, reject) => requests.push({ args, resolve, reject })) },
    apiClient: { post(...args) { return new Promise((resolve, reject) => summaries.push({ args, resolve, reject })) } },
  })
  let files = [], errors = [], paused = false
  const coordinator = new DirectoryCoordinator('outputs', (value, failures) => { files = value; errors = failures }, () => {}, value => { paused = value })
  const tick = async () => { const [key, timer] = timers.entries().next().value || []; if (timer) { timers.delete(key); timer.callback(); await flush() } }
  return { coordinator, DirectoryCoordinator, utils, clock, requests, summaries, timers, tick, get files() { return files }, get errors() { return errors }, get paused() { return paused } }
}
const file = (name, extra = {}) => ({ name, type: 'file', created_at: 1, bytes: 10, file_version: 'v1', index_generation: 1, ...extra })

test('切目录取消旧请求，多目录成功独立保留，失败清除旧结果，空选择保持空列表', async () => {
  const h = await harness()
  const first = h.coordinator.load(['old'])
  const second = h.coordinator.load(['new', 'bad'])
  assert.equal(h.requests[0].args[2].aborted, true)
  h.requests[0].resolve({ files: [file('old.png')] }); await first
  assert.equal(h.files.length, 0)
  h.requests[1].resolve({ files: [file('new.png')] }); h.requests[2].reject(Error('failed')); await second
  assert.equal(h.files[0].name, 'new.png'); assert.deepEqual([...h.errors], ['bad'])
  await h.coordinator.load([]); assert.equal(h.files.length, 0)
  h.coordinator.stop()
})

test('真实响应式搜索隐藏的待处理全集轮转补齐，对象身份保持且可见变更不重复订阅', async () => {
  const h = await harness()
  const loading = h.coordinator.load([''])
  h.requests[0].resolve({ files: Array.from({ length: 450 }, (_, i) => file(`${i}.png`, { metadata_pending: true })) }); await loading
  const original = h.files[0]
  const matches = Vue.computed(() => h.files.filter(f => f.summary?.models?.includes('target')))
  const counts = []
  const stop = Vue.watch(matches, value => counts.push(value.length))
  h.coordinator.setVisible(h.files.slice(0, 20)); await h.tick()
  assert.equal(h.summaries.length, 1); assert.equal(h.summaries[0].args[1].files.length, 200)
  h.coordinator.setVisible(h.files.slice(20, 40)); await h.tick()
  assert.equal(h.summaries.length, 1)
  h.summaries[0].resolve({ data: { files: h.summaries[0].args[1].files.map(f => ({ ...f, status: 'complete', summary: { models: ['target'] } })) } }); await flush()
  assert.equal(matches.value.length, 200); assert.equal(h.files[0], original)
  await h.tick(); assert.equal(h.summaries[1].args[1].files[0].name, '200.png')
  h.summaries[1].resolve({ data: { files: h.summaries[1].args[1].files.map(f => ({ ...f, status: 'complete' })) } }); await flush()
  await h.tick(); assert.equal(h.summaries[2].args[1].files.length, 50)
  h.summaries[2].resolve({ data: { files: h.summaries[2].args[1].files.map(f => ({ ...f, status: 'complete' })) } }); await flush(); await h.tick()
  assert.equal(h.summaries.length, 3); assert.ok(counts.includes(200))
  stop(); h.coordinator.stop()
})

test('摘要网络失败使用1/2/4秒退避并暂停，页面重试恢复', async () => {
  const h = await harness(), loading = h.coordinator.load([''])
  h.requests[0].resolve({ files: [file('a.png', { metadata_pending: true })] }); await loading
  await h.tick()
  for (let i = 0; i < 3; i++) {
    h.summaries[i].reject(Error('network')); await flush()
    assert.equal([...h.timers.values()][0].delay, 1000 * 2 ** i); await h.tick()
  }
  assert.equal(h.paused, true); assert.equal(h.timers.size, 0)
  h.coordinator.retry(); await h.tick(); assert.equal(h.summaries.length, 4)
  h.coordinator.stop()
})

function renderer() {
  const node = () => ({ children: [], parent: null, style: {}, classList: { add() {}, remove() {} }, addEventListener() {}, removeEventListener() {}, setAttribute() {}, removeAttribute() {}, getBoundingClientRect: () => ({ width: 200, height: 30 }), querySelector: () => null, querySelectorAll: () => [], focus() {}, blur() {}, contains: () => false })
  return Vue.createRenderer({ createElement: node, createText: node, createComment: node, setText() {}, setElementText() {}, patchProp() {}, parentNode: n => n.parent, nextSibling: () => null,
    insert(n, parent) { n.parent = parent; parent.children.push(n) }, remove(n) { if (n.parent) n.parent.children = n.parent.children.filter(v => v !== n) } })
}

test('真实KeepAlive停用取消目录和摘要，激活仅恢复一次，卸载解绑事件', async () => {
  const h = await harness(), events = new Map()
  const mixin = (await loadModule('../src/utils/directory-page.ts', { DirectoryCoordinator: h.DirectoryCoordinator, window: { top: { addEventListener: (key, fn) => events.set(key, fn), removeEventListener: key => events.delete(key) } } })).default
  const shown = Vue.ref(true)
  let page
  const Page = Vue.defineComponent({ mixins: [mixin], data: () => ({ allFiles: [], loading: false }), mounted() { page = this; this.registerBrowserShow(); this.loadFiles() }, methods: { loadFiles() { return this.loadDirectoryScope('outputs', ['']) } }, render: () => Vue.h('div') })
  const app = renderer().createApp({ render: () => Vue.h(Vue.KeepAlive, null, { default: () => shown.value ? Vue.h(Page) : null }) })
  app.mount({ children: [] }); await flush(); assert.equal(h.requests.length, 1)
  shown.value = false; await flush(); assert.equal(h.requests[0].args[2].aborted, true)
  events.get('comfyuiBrowserShow')(); assert.equal(h.requests.length, 1)
  h.requests[0].resolve({ files: [file('late.png')] }); await flush(); assert.equal(page.allFiles.length, 0)
  shown.value = true; await flush(); assert.equal(h.requests.length, 2)
  h.requests[1].resolve({ files: [file('ready.png', { metadata_pending: true })] }); await flush(); await h.tick(); assert.equal(h.summaries.length, 1)
  shown.value = false; await flush(); assert.equal(h.summaries[0].args[2].signal.aborted, true)
  app.unmount(); assert.equal(events.size, 0)
})

test('同名媒体线性预处理按目录隔离且逐段编码URL，选择身份不碰撞', async () => {
  const h = await harness()
  const files = Array.from({ length: 1000 }, (_, i) => [file(`${i} #中.png`), file(`${i} #中.json`)]).flat()
  const processed = h.utils.processDirectoryFiles(files, 'outputs', 'a #/b')
  assert.equal(processed.length, 1000)
  assert.equal(processed[0].url, '/browser/s/outputs/a%20%23/b/0%20%23%E4%B8%AD.json')
  assert.notEqual(h.utils.fileIdentity('outputs', file('x', { folder_path: 'a/b' })), h.utils.fileIdentity('outputs', file('b/x', { folder_path: 'a' })))
})

test('FileCardList真实watcher使用摘要搜索，刷新保页，范围变化关闭详情并清选择', async () => {
  const h = await harness()
  const bindings = { ...h.utils, i18n: { global: { t: key => key } }, fetchAllTags: async () => [] }
  for (const name of ['Folder','Document','Search','ZoomIn','ZoomOut','Plus','Filter','Menu','Grid','Refresh','FileThumbnail','ImagePreviewDialog','ElInput','ElSelect','ElOption','ElTag','ElTooltip','ElButton','ElButtonGroup','ElSlider','ElPagination','ElImage','ElIcon','ElCheckbox','ElEmpty']) bindings[name] = {}
  const Card = (await loadModule('../src/components/Common/FileCardList.vue', bindings)).default
  Card.render = () => Vue.h('div')
  const files = Vue.ref(Array.from({ length: 50 }, (_, i) => file(`${i}.png`, { fileType: 'image' })))
  const scope = Vue.ref(1), visible = []
  let card
  const app = renderer().createApp({ render: () => Vue.h(Card, { ref: value => { card = value }, folderType: 'outputs', files: files.value, scopeRevision: scope.value, onVisibleFiles: value => visible.push(value) }) })
  app.mount({ children: [] }); await flush()
  card.currentPage = 2; await flush()
  files.value = files.value.map(f => ({ ...f })); await flush(); assert.equal(card.currentPage, 2)
  card.internalSearchQuery = 'target'; await flush(); assert.equal(card.filteredFiles.length, 0)
  files.value[42].summary = { models: ['target'] }; await flush(); assert.equal(card.filteredFiles.length, 1)
  const count = visible.length; await flush(); await flush(); assert.equal(visible.length, count)
  card.showImagePreview = true; card.selectedFiles.add(card.getFileKey(files.value[42])); scope.value++; await flush()
  assert.equal(card.showImagePreview, false); assert.equal(card.selectedFiles.size, 0); assert.equal(card.currentPage, 1)
  app.unmount()
})

test('缩略图409请求刷新版本，失败同版本仅回退一次，DPR档位及停用取消生效', async () => {
  const requests = [], stale = [], revoked = []
  const Thumbnail = (await loadModule('../src/components/Common/FileThumbnail.vue', {
    window: { devicePixelRatio: 2 }, URLSearchParams,
    URL: { createObjectURL: () => 'blob:thumbnail', revokeObjectURL: url => revoked.push(url) },
    fetch(...args) { return new Promise((resolve, reject) => requests.push({ args, resolve, reject })) },
  })).default
  Thumbnail.render = () => Vue.h('img')
  const shown = Vue.ref(true), current = Vue.ref(file('a.png', { previewUrl: '/original' }))
  let thumbnail
  const app = renderer().createApp({ render: () => Vue.h(Vue.KeepAlive, null, { default: () => shown.value ? Vue.h(Thumbnail, { ref: value => { if (value) thumbnail = value }, file: current.value, folderType: 'outputs', displaySize: 200, onStale: () => stale.push(true) }) : null }) })
  app.mount({ children: [] }); await flush(); assert.equal(requests.length, 1); assert.match(requests[0].args[0], /size=512/)
  requests[0].resolve({ status: 409 }); await flush(); assert.equal(stale.length, 1); assert.equal(thumbnail.imageUrl, '')
  current.value.file_version = 'v2'; await flush(); requests[1].reject(Error('network')); await flush(); assert.equal(thumbnail.imageUrl, '/original')
  thumbnail.imageUrl = 'failed-original'; thumbnail.fallbackOriginal(); assert.equal(thumbnail.imageUrl, 'failed-original')
  current.value.file_version = 'v3'; await flush(); assert.equal(requests.length, 3)
  shown.value = false; await flush(); assert.equal(requests[2].args[1].signal.aborted, true)
  shown.value = true; await flush(); assert.equal(requests.length, 4)
  requests[3].resolve({ ok: true, status: 200, blob: async () => ({}) }); await flush(); assert.equal(thumbnail.imageUrl, 'blob:thumbnail')
  app.unmount(); assert.ok(revoked.includes('blob:thumbnail'))
})

test('缩略图仅进入视口后请求，离开视口与KeepAlive停用取消并断开观察', async () => {
  const requests = [], observers = []
  class IntersectionObserver {
    constructor(callback) { this.callback = callback; this.disconnected = false; observers.push(this) }
    observe() {}
    disconnect() { this.disconnected = true }
  }
  const Thumbnail = (await loadModule('../src/components/Common/FileThumbnail.vue', { IntersectionObserver, window: { devicePixelRatio: 1 }, URLSearchParams, URL, fetch(...args) { return new Promise(resolve => requests.push({ args, resolve })) } })).default
  Thumbnail.render = () => Vue.h('div')
  const shown = Vue.ref(true)
  const app = renderer().createApp({ render: () => Vue.h(Vue.KeepAlive, null, { default: () => shown.value ? Vue.h(Thumbnail, { file: file('a.png'), folderType: 'outputs' }) : null }) })
  app.mount({ children: [] }); await flush(); assert.equal(requests.length, 0)
  observers[0].callback([{ isIntersecting: true }]); await flush(); assert.equal(requests.length, 1)
  observers[0].callback([{ isIntersecting: false }]); assert.equal(requests[0].args[1].signal.aborted, true)
  shown.value = false; await flush(); assert.equal(observers[0].disconnected, true)
  shown.value = true; await flush(); assert.equal(observers.length, 2); assert.equal(requests.length, 1)
  observers[1].callback([{ isIntersecting: true }]); await flush(); assert.equal(requests.length, 2)
  app.unmount(); assert.equal(observers[1].disconnected, true)
})

test('详情真实watcher按身份与版本订阅，摘要更新不重订阅，KeepAlive停用清理', async () => {
  const subscriptions = []
  const Preview = (await loadModule('../src/components/Common/ImagePreviewDialog/ImagePreviewDialog.vue', {
    ElImageViewer: {}, Close: {}, MetadataProperties: {}, i18n: { global: { t: key => key } },
    subscribeMetadata(...args) { const entry = { args, stopped: false }; subscriptions.push(entry); return () => { entry.stopped = true } },
  })).default
  Preview.render = () => Vue.h('div')
  const files = Vue.ref([file('a.png'), file('b.png')]), selected = Vue.ref(0), shown = Vue.ref(true)
  const app = renderer().createApp({ render: () => Vue.h(Vue.KeepAlive, null, { default: () => shown.value ? Vue.h(Preview, { modelValue: true, previewFileList: files.value, initialIndex: selected.value, folderType: 'outputs' }) : null }) })
  app.mount({ children: [] }); await flush(); assert.equal(subscriptions.length, 1)
  files.value[0].summary = { models: ['updated'] }; await flush(); assert.equal(subscriptions.length, 1)
  selected.value = 1; await flush(); assert.equal(subscriptions.length, 2); assert.equal(subscriptions[0].stopped, true)
  files.value[1].index_generation = 2; await flush(); assert.equal(subscriptions.length, 3)
  shown.value = false; await flush(); assert.equal(subscriptions[2].stopped, true)
  shown.value = true; await flush(); assert.equal(subscriptions.length, 4)
  app.unmount(); assert.equal(subscriptions[3].stopped, true)
})

test('后台重建固定当前层与显式范围、失败计数、过期状态以及停用创建恢复', async () => {
  const h = await harness(), jobs = []
  const mixin = (await loadModule('../src/utils/directory-page.ts', { ...h.clock, DirectoryCoordinator: h.DirectoryCoordinator, window: { top: { removeEventListener() {} } }, apiClient: {
    post(...args) { return new Promise((resolve, reject) => jobs.push({ args, resolve, reject })) },
    get(...args) { return new Promise((resolve, reject) => jobs.push({ args, resolve, reject })) },
  } })).default
  let page
  const Page = Vue.defineComponent({ mixins: [mixin], mounted() { page = this; this.directoryScope = JSON.stringify(['outputs', ['a', 'b']]) }, methods: { loadFiles() {} }, render: () => Vue.h('div') })
  const app = renderer().createApp(Page); app.mount({ children: [] })
  const creating = page.startReindex(); assert.deepEqual(Object.keys(jobs[0].args[1]).sort(), ['folder_paths', 'folder_type']); assert.deepEqual([...jobs[0].args[1].folder_paths], ['a', 'b'])
  page.stopDirectoryRequests(); assert.equal(jobs[0].args[2].signal.aborted, true); assert.equal(page.reindexStatus, 'unknown')
  jobs[0].resolve({ data: { job_id: 'late' } }); await creating; assert.equal(page.reindexJobId, '')
  page.directoryActive = true
  const retry = page.startReindex(); assert.deepEqual(Object.keys(jobs[1].args[1]).sort(), ['folder_paths', 'folder_type'])
  jobs[1].resolve({ data: { job_id: 'current' } }); await retry; assert.equal(jobs.length, 3)
  jobs[2].resolve({ data: { status: 'complete', success_count: 3, failed_count: 1, superseded_count: 2 } }); await flush()
  assert.equal(page.reindexCounts.failed_count, 1); assert.equal(page.reindexCounts.superseded_count, 2)
  page.reindexJobId = 'expired'; const polling = page.pollReindex(); jobs[3].reject({ response: { status: 404 } }); await polling
  assert.equal(page.reindexStatus, 'expired')
  page.requestScopeRefresh(); page.stopDirectoryRequests(); assert.equal(page.refreshTimer, undefined)
  app.unmount()
})

test('新目录慢加载时旧摘要取消及finally保持隔离，不发送旧pending或重启列表', async () => {
  const h = await harness(), stale = []
  h.coordinator.stale = paths => stale.push(paths)
  const first = h.coordinator.load(['old'])
  h.requests[0].resolve({ files: [file('old.png', { metadata_pending: true })] }); await first; await h.tick()
  assert.equal(h.summaries.length, 1)
  const next = h.coordinator.load(['new'])
  assert.equal(h.coordinator.pending.size, 0); assert.equal(h.coordinator.files.length, 0)
  assert.equal(h.summaries[0].args[2].signal.aborted, true)
  h.summaries[0].resolve({ data: { files: [{ ...h.summaries[0].args[1].files[0], status: 'stale' }] } }); await flush()
  await h.tick(); await h.tick()
  assert.equal(h.summaries.length, 1); assert.equal(h.timers.size, 0); assert.equal(stale.length, 0)
  assert.equal(h.requests[1].args[2].aborted, false)
  h.requests[1].resolve({ files: [file('new.png', { metadata_pending: true })] }); await next; await h.tick()
  assert.equal(h.summaries.length, 2); assert.equal(h.summaries[1].args[1].files[0].folder_path, 'new')
  h.coordinator.stop()
})

test('新代次摘要已在途时旧请求finally不能释放新请求锁', async () => {
  const h = await harness()
  let loading = h.coordinator.load(['old']); h.requests[0].resolve({ files: [file('old.png', { metadata_pending: true })] }); await loading; await h.tick()
  loading = h.coordinator.load(['new']); h.requests[1].resolve({ files: [file('new.png', { metadata_pending: true })] }); await loading; await h.tick()
  const currentController = h.coordinator.summaryController
  h.summaries[0].resolve({ data: { files: [] } }); await flush()
  assert.equal(h.coordinator.running, true); assert.equal(h.coordinator.summaryController, currentController)
  h.coordinator.setVisible(h.files); await h.tick(); assert.equal(h.summaries.length, 2)
  h.coordinator.stop()
})

test('多目录stale仅刷新失效目录，其他目录对象及pending轮转进度保持', async () => {
  const h = await harness(), stale = []
  h.coordinator.stale = paths => stale.push(paths)
  const loading = h.coordinator.load(['a', 'b'])
  h.requests[0].resolve({ files: [file('a.png', { metadata_pending: true })] })
  h.requests[1].resolve({ files: [file('b.png', { metadata_pending: true })] }); await loading
  const b = h.files.find(file => file.folder_path === 'b')
  await h.tick()
  h.summaries[0].resolve({ data: { files: [ { ...h.summaries[0].args[1].files[0], status: 'stale' }, { ...h.summaries[0].args[1].files[1], status: 'processing', summary: { models: ['retained'] } } ] } }); await flush()
  assert.deepEqual([...stale[0]], ['a'])
  const refresh = h.coordinator.refreshDirectories(['a', 'a'])
  assert.equal(h.requests.length, 3); assert.equal(h.requests[2].args[1], 'a')
  assert.equal(h.coordinator.pending.size, 1); assert.equal([...h.coordinator.pending.values()][0], b)
  h.requests[2].resolve({ files: [file('a.png', { file_version: 'v2', metadata_pending: true })] }); await refresh
  assert.equal(h.files.find(file => file.folder_path === 'b'), b)
  assert.equal(b.summary.models[0], 'retained')
  assert.equal([...h.coordinator.pending.values()][0], b)
  assert.equal(h.files.find(file => file.folder_path === 'a').file_version, 'v2')
  h.coordinator.stop()
})

test('页面50ms合并摘要、缩略图、详情的失效目录集合并局部刷新', async () => {
  const h = await harness(), refreshed = []
  const mixin = (await loadModule('../src/utils/directory-page.ts', { ...h.clock, DirectoryCoordinator: h.DirectoryCoordinator, window: { top: { removeEventListener() {} } } })).default
  let page
  const app = renderer().createApp({ mixins: [mixin], mounted() { page = this; this.directoryCoordinator = Vue.markRaw({ refreshDirectories: paths => refreshed.push(paths), stop() {} }) }, render: () => Vue.h('div') })
  app.mount({ children: [] })
  page.requestScopeRefresh(['a']); page.requestScopeRefresh('b'); page.requestScopeRefresh('a')
  assert.equal(h.timers.size, 1); assert.equal([...h.timers.values()][0].delay, 50)
  await h.tick(); assert.deepEqual([...refreshed[0]], ['a', 'b'])
  app.unmount()
})

test('真实ElementPlus多选标签关闭后空数组保持无标签', async t => {
  const keys = ['document', 'window', 'Element', 'HTMLElement', 'MouseEvent']
  const originals = new Map(keys.map(key => [key, Object.getOwnPropertyDescriptor(globalThis, key)]))
  t.after(() => { for (const key of keys) { const descriptor = originals.get(key); if (descriptor) Object.defineProperty(globalThis, key, descriptor); else delete globalThis[key] } })
  globalThis.MouseEvent = class { stopPropagation() {} }
  const { ElSelect, ElOption, ID_INJECTION_KEY } = await import('element-plus')
  globalThis.document = { addEventListener() {}, removeEventListener() {}, activeElement: null }
  globalThis.window = { setTimeout, clearTimeout, HTMLElement: class {}, Element: class {}, getComputedStyle: () => ({ getPropertyValue: () => '', width: '200px' }) }
  globalThis.Element = window.Element
  globalThis.HTMLElement = window.HTMLElement
  const opened = []
  const selected = Vue.ref([''])
  let select
  const app = renderer().createApp({ render: () => Vue.h(ElSelect, { ref: value => { select = value }, modelValue: selected.value, multiple: true, clearable: true, teleported: false, persistent: false, 'onUpdate:modelValue': value => { selected.value = value } }, { default: () => Vue.h(ElOption, { value: '', label: '输出根目录' }), label: ({ label, value }) => Vue.h('span', { 'data-test': 'directory-label', onClick: event => { event.stopPropagation(); opened.push(value) } }, label) }) })
  app.provide(ID_INJECTION_KEY, { prefix: 1, current: 0 }); app.config.warnHandler = () => {}
  app.mount({ children: [] }); await flush()
  assert.equal(select.states.selected.length, 1)
  const tags = vnode => {
    if (!vnode) return []
    return [...(vnode.type?.name === 'ElTag' ? [vnode] : []), ...tags(vnode.component?.subTree), ...(Array.isArray(vnode.children) ? vnode.children.flatMap(tags) : [])]
  }
  assert.equal(tags(select.$.subTree).length, 1)
  const labels = vnode => !vnode ? [] : [...(vnode.props?.['data-test'] === 'directory-label' ? [vnode] : []), ...labels(vnode.component?.subTree), ...(Array.isArray(vnode.children) ? vnode.children.flatMap(labels) : [])]
  labels(select.$.subTree)[0].props.onClick(new MouseEvent())
  assert.deepEqual(opened, ['']); assert.deepEqual([...selected.value], [''])
  tags(select.$.subTree)[0].component.emit('close', new MouseEvent())
  await flush()
  assert.deepEqual([...selected.value], [])
  assert.equal(select.states.selected.length, 0)
  assert.equal(tags(select.$.subTree).length, 0)
  app.unmount()
})

async function outputsHarness(preferences, fetchRegistry) {
  const h = await harness(), store = new Map(), registered = [], opened = []
  if (preferences !== undefined) store.set('comfyui-browser', JSON.stringify({ directories: { 'outputs-file-list': preferences } }))
  const utils = await loadModule('../src/utils/index.ts', { localStorage: { getItem: key => store.get(key) ?? null, setItem: (key, value) => store.set(key, value) } })
  const window = { top: { addEventListener() {}, removeEventListener() {} } }
  const directoryPage = (await loadModule('../src/utils/directory-page.ts', { DirectoryCoordinator: h.DirectoryCoordinator, window })).default
  const output = (await loadModule('../src/components/Files/FilesTab.vue', { ...utils, directoryPage, window,
    i18n: { global: { t: key => key } }, ElMessage: {}, ElMessageBox: {}, Delete: {}, FolderOpened: {}, Grid: {}, Menu: {}, FileCardList: {},
    openFolderOnSystem: async (...args) => opened.push(args),
    getBrowserConfig: async () => ({ outputs: 'D:/output' }), fetchRegisteredDirectories: fetchRegistry || (async () => registered),
    registerDirectory: async path => { registered.push({ path: '@external/opaque', absolute_path: path, name: '中文目录' }); return registered.at(-1) },
  })).default
  output.render = () => Vue.h('div')
  output.mounted = function () {}
  let page
  const app = renderer().createApp({ render: () => Vue.h(output, { ref: value => { page = value } }) })
  app.mount({ children: [] }); await flush()
  return { ...h, utils, store, registered, page, app, output, opened }
}

test('输出首次访问默认root，明确空偏好及取消最后选择刷新后保持空且不发列表请求', async () => {
  const h = await outputsHarness()
  h.page.restoreDirectories(); assert.deepEqual([...h.page.selectedDirectoryKeys], [''])
  h.page.directoriesReady = true
  h.page.handleDirectorySelectionChange([]); await flush()
  assert.equal(h.requests.length, 0); assert.equal(h.page.allFiles.length, 0)
  h.page.restoreDirectories(); assert.deepEqual([...h.page.selectedDirectoryKeys], [])
  assert.equal(h.utils.hasDirectoryPreferences('outputs-file-list'), true)
  h.utils.setDirectoryPreferences('outputs-file-list', [])
  h.page.restoreDirectories(); assert.deepEqual([...h.page.selectedDirectoryKeys], [])
  h.app.unmount()
})

test('输出注册服务器绝对目录保留虚拟路径，重新读取注册信息恢复标签和绝对路径', async () => {
  const h = await outputsHarness([])
  h.page.restoreDirectories(); h.page.directoriesReady = true; h.page.newDirectoryInput = 'E:/中文 目录#'
  const adding = h.page.handleAddDirectory(); await flush()
  assert.equal(h.requests.length, 1); assert.equal(h.requests[0].args[1], '@external/opaque')
  h.requests[0].resolve({ files: [file('image.png'), { ...file('child'), type: 'dir' }] }); await adding
  assert.equal(h.page.allFiles.length, 1); assert.equal(h.page.allFiles[0].name, 'image.png')
  h.page.registeredDirectories = h.registered; h.page.restoreDirectories()
  assert.equal(h.page.managedDirectories.find(dir => dir.relativePath === '@external/opaque').absolutePath, 'E:/中文 目录#')
  assert.equal(h.page.managedDirectories.find(dir => dir.relativePath === '@external/opaque').relativePath, '@external/opaque')
  assert.equal(h.page.managedDirectories.find(dir => dir.relativePath === '@external/opaque').name, '中文目录')
  assert.equal(h.requests.length, 1)
  h.app.unmount()
})

test('外部目录原图与配套JSON使用view接口编码，内部静态路径保持', async () => {
  const h = await harness()
  const result = h.utils.processDirectoryFiles([file('中文 #.png'), file('中文 #.json')], 'outputs', '@external/abc')
  const preview = new URL(result[0].previewUrl, 'http://test'), workflow = new URL(result[0].url, 'http://test')
  assert.equal(preview.pathname, '/browser/files/view'); assert.equal(preview.searchParams.get('folder_path'), '@external/abc')
  assert.equal(preview.searchParams.get('filename'), '中文 #.png'); assert.equal(workflow.searchParams.get('filename'), '中文 #.json')
  assert.equal(h.utils.getFileUrl('outputs', file('a.png', { folder_path: 'normal' })), '/browser/s/outputs/normal/a.png')
})

test('输出KeepAlive取消注册目录读取，激活恢复一次且迟到响应不能覆盖新配置', async () => {
  const registries = []
  const h = await outputsHarness(undefined, signal => new Promise(resolve => registries.push({ signal, resolve })))
  h.app.unmount()
  h.output.mounted = function () { this.initializeDirectories() }
  const shown = Vue.ref(true)
  let page
  const app = renderer().createApp({ render: () => Vue.h(Vue.KeepAlive, null, { default: () => shown.value ? Vue.h(h.output, { ref: value => { if (value) page = value } }) : null }) })
  app.mount({ children: [] }); await flush(); assert.equal(registries.length, 1)
  shown.value = false; await flush(); assert.equal(registries[0].signal.aborted, true)
  shown.value = true; await flush(); assert.equal(registries.length, 2)
  registries[0].resolve([{ path: '@external/old', absolute_path: 'E:/old', name: '旧目录' }]); await flush()
  assert.equal(page.registeredDirectories.length, 0); assert.equal(page.initializingDirectories, true)
  registries[1].resolve([{ path: '@external/new', absolute_path: 'E:/new', name: '新目录' }]); await flush()
  assert.equal(h.requests.length, 1); h.requests[0].resolve({ files: [] }); await flush()
  assert.equal(page.registeredDirectories[0].path, '@external/new'); assert.equal(page.initializingDirectories, false)
  app.unmount()
})

test('目录注册接口失败显示统一错误且不把缺失注册表标记为成功', async () => {
  const h = await outputsHarness([{ path: 'saved', checked: true }], async () => { throw { response: { status: 404 } } })
  await h.page.initializeDirectories()
  assert.equal(h.page.directoriesReady, false)
  assert.equal(h.requests.length, 0)
  assert.equal(h.page.directorySetupError, '读取目录配置失败，请重试。')
  assert.deepEqual([...h.utils.getDirectoryPreferences('outputs-file-list')].map(pref => pref.path), ['saved'])
  h.app.unmount()
})

test('注册表失败保持明确空选择，重试成功不改动已保存选择', async () => {
  let failed = true
  const h = await outputsHarness([], async () => { if (failed) throw Error('network'); return [{ path: '@external/new', name: '新目录', absolute_path: 'E:/new' }] })
  await h.page.initializeDirectories()
  assert.equal(h.requests.length, 0); assert.deepEqual([...h.page.selectedDirectoryKeys], [])
  assert.equal(h.page.directorySetupError, '读取目录配置失败，请重试。')
  assert.equal(h.page.directoriesReady, false)
  failed = false; await h.page.initializeDirectories()
  assert.equal(h.page.directorySetupError, ''); assert.deepEqual([...h.page.selectedDirectoryKeys], [])
  assert.equal(h.page.managedDirectories.some(dir => dir.relativePath === '@external/new'), true)
  assert.equal(h.requests.length, 0)
  h.app.unmount()
})

test('文件列表仅发送目录范围，不再发送摘要格式切换参数', async () => {
  const requests = []
  const api = await loadModule('../src/api/files.ts', { apiClient: { get: async (...args) => { requests.push(args); return { data: { files: [] } } } } })
  await api.fetchFilesList('outputs', 'images')
  assert.deepEqual(Object.keys(requests[0][1].params).sort(), ['folder_path', 'folder_type'])
})
