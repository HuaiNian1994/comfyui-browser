import test from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import vm from 'node:vm'
import ts from 'typescript'

const source = await readFile(new URL('../src/components/Files/FilesTab.vue', import.meta.url), 'utf8')
const script = source.match(/<script lang="ts">([\s\S]*?)<\/script>/)[1]
const tree = ts.createSourceFile('component.ts', script, ts.ScriptTarget.Latest, true, ts.ScriptKind.TS)
const options = tree.statements.find(ts.isExportAssignment).expression.arguments[0]
const methods = options.properties.find(p => p.name?.getText(tree) === 'methods').initializer
const load = methods.properties.find(p => p.name?.getText(tree) === 'loadFiles')
const unmount = options.properties.find(p => p.name?.getText(tree) === 'beforeUnmount')
const code = ts.transpileModule(`const component = {${load.getText(tree)},${unmount.getText(tree)}}`, {
  compilerOptions: { target: ts.ScriptTarget.ES2020 },
}).outputText

function harness() {
  const requests = []
  const context = vm.createContext({ AbortController, console,
    fetchFilesList(...args) { return new Promise((resolve, reject) => requests.push({ args, resolve, reject })) },
    processFileInfo: file => file, processDirectoryInfo: file => file,
  })
  vm.runInContext(`${code}\nglobalThis.component = component`, context)
  const state = { directoryListId: 'outputs', directoriesReady: true, currentFolderPath: '', folderType: 'outputs',
    filesRequestGeneration: 0, filesAbortController: null, loading: false, allFiles: [], targets: ['old'],
    getTargetFolderPaths() { return this.targets },
  }
  return { state, requests, load: () => context.component.loadFiles.call(state), unmount: () => context.component.beforeUnmount.call(state) }
}

test('切目录取消旧请求，旧结果与结束状态不覆盖新目录', async () => {
  const h = harness()
  const old = h.load()
  h.state.targets = ['new']
  const current = h.load()
  assert.equal(h.requests[0].args[2].aborted, true)
  h.requests[0].resolve({ files: [{ name: 'old.png', type: 'file' }] })
  await old
  assert.equal(h.state.loading, true)
  assert.equal(h.state.allFiles.length, 0)
  h.requests[1].resolve({ files: [{ name: 'new.png', type: 'file' }] })
  await current
  assert.equal(h.state.allFiles[0].name, 'new.png')
  assert.equal(h.state.loading, false)
})

test('离开页面取消请求，迟到响应不能更新文件列表', async () => {
  const h = harness()
  const loading = h.load()
  h.unmount()
  assert.equal(h.requests[0].args[2].aborted, true)
  h.requests[0].resolve({ files: [{ name: 'late.png', type: 'file' }] })
  await loading
  assert.equal(h.state.allFiles.length, 0)
})
