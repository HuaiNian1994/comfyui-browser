import test from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import vm from 'node:vm'
import ts from 'typescript'

async function harness() {
  const requests = []
  const timers = new Map()
  let timerId = 0
  const source = await readFile(new URL('../src/api/metadata-subscription.ts', import.meta.url), 'utf8')
  const code = ts.transpileModule(source.replace(/import[^\n]+\n/g, '').replace('export function', 'function'), {
    compilerOptions: { target: ts.ScriptTarget.ES2020 },
  }).outputText
  const context = vm.createContext({
    AbortController, console,
    setTimeout(callback) { const id = ++timerId; timers.set(id, callback); return id },
    clearTimeout(id) { timers.delete(id) },
    fetchImageMetadata(...args) { return new Promise((resolve, reject) => requests.push({ args, resolve, reject })) },
  })
  vm.runInContext(code, context)
  return { subscribe: context.subscribeMetadata, requests, timers }
}

const ready = { positive: '', negative: '', has_metadata: true, index_status: 'complete' }
const flush = () => new Promise(resolve => setImmediate(resolve))

test('列表与详情共享请求，完成后停止轮询', async () => {
  const h = await harness()
  const first = [], second = []
  const stopA = h.subscribe('outputs', 'one.png', '', value => first.push(value))
  const stopB = h.subscribe('outputs', 'one.png', '', value => second.push(value))
  assert.equal(h.requests.length, 1)
  h.requests[0].resolve(ready)
  await flush()
  assert.equal(first.length, 1)
  assert.equal(second.length, 1)
  assert.equal(h.timers.size, 0)
  stopA(); stopB()
})

test('等待结果触发只读轮询，关闭最后订阅清理计时器', async () => {
  const h = await harness()
  const stop = h.subscribe('outputs', 'one.png', '', () => {})
  h.requests[0].resolve({ ...ready, index_status: 'processing' })
  await flush()
  assert.equal(h.timers.size, 1)
  const [id, callback] = h.timers.entries().next().value
  h.timers.delete(id); callback()
  assert.equal(h.requests[1].args[3].poll, true)
  stop()
  assert.equal(h.requests[1].args[3].signal.aborted, true)
  h.requests[1].resolve(ready)
  await flush()
  assert.equal(h.timers.size, 0)
})

test('刷新后的结果覆盖旧请求，过期响应无法写回', async () => {
  const h = await harness()
  const values = []
  const stopA = h.subscribe('outputs', 'one.png', '', value => values.push(value))
  const stopB = h.subscribe('outputs', 'one.png', '', () => {}, true)
  assert.equal(h.requests[0].args[3].signal.aborted, true)
  assert.equal(h.requests[1].args[3].refresh, true)
  h.requests[1].resolve({ ...ready, positive: 'new' }); await flush()
  h.requests[0].resolve({ ...ready, positive: 'old' }); await flush()
  assert.equal(values.length, 1)
  assert.equal(values[0].positive, 'new')
  stopA(); stopB()
})

test('切图后旧图片响应不更新已释放的订阅', async () => {
  const h = await harness()
  const values = []
  const stopA = h.subscribe('outputs', 'one.png', '', value => values.push(value))
  stopA()
  const stopB = h.subscribe('outputs', 'two.png', '', value => values.push(value))
  h.requests[0].resolve({ ...ready, positive: 'old' }); await flush()
  h.requests[1].resolve({ ...ready, positive: 'new' }); await flush()
  assert.deepEqual(values.map(value => value.positive), ['new'])
  stopB()
})
