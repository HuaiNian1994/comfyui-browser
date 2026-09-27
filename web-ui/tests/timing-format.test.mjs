import test from 'node:test'
import assert from 'node:assert/strict'
import vm from 'node:vm'
import { readFile } from 'node:fs/promises'
import ts from 'typescript'
const source = await readFile(new URL('../src/components/Common/ImagePreviewDialog/utils/timing-format.ts', import.meta.url), 'utf8')
const context = vm.createContext({})
vm.runInContext(ts.transpileModule(source.replace(/import[^\n]+\n/g, '').replace(/export /g, ''), { compilerOptions: { target: ts.ScriptTarget.ES2020 } }).outputText, context)
test('秒与分钟按原值切换，小数不进位跨过边界', () => {
  const f = value => context.formatDuration(value, '秒', '分钟')
  assert.equal(f(59999), '59.99 秒'); assert.equal(f(60000), '1 分钟')
  assert.equal(f(0), '0 秒'); assert.equal(f(1), '<0.01 秒'); assert.equal(f(138000), '2.3 分钟')
})
test('缓存零步与未知步数隐藏速度，真实步数决定速度', () => {
  assert.equal(context.timingValues().length, 0)
  assert.equal(context.timingValues({ total_ms: 1000, sampling_ms: 0, iterations: 0 }).length, 1)
  assert.equal(context.timingValues({ total_ms: 1000, sampling_ms: 600 }).length, 2)
  assert.equal(context.timingValues({ total_ms: 1000, sampling_ms: 600, iterations: 3 })[2].value, 200)
  assert.equal(context.timingValues({ total_ms: NaN }).length, 0)
})
