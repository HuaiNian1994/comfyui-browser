import test from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import vm from 'node:vm'
import ts from 'typescript'

const source = await readFile(new URL('../src/components/Common/ImagePreviewDialog/utils/metadata-sections.ts', import.meta.url), 'utf8')
const code = ts.transpileModule(source.replace(/import[^\n]+\n/g, '').replace(/export /g, ''), { compilerOptions: { target: ts.ScriptTarget.ES2020 } }).outputText
const context = vm.createContext({})
vm.runInContext(code, context)
const stage = id => ({ id, node_id: id, class_type: 'KSampler', kind: 'sampling', properties: [], depends_on: [] })
const branch = (id, stage_ids) => ({ id, stage_ids, association: 'unconfirmed' })
const build = (branches, stages) => JSON.parse(JSON.stringify(context.buildMetadataSections(branches, stages)))

test('共享上游只展示一次，分支保留各自后续步骤与引用', () => {
  const result = build([branch('55', ['86', '88', '24', '26']), branch('73', ['86', '88', '24'])], ['86', '88', '24', '26'].map(stage))
  assert.deepEqual(result.map(s => s.stages.map(x => x.id)), [['86', '88', '24'], ['26'], []])
  assert.deepEqual(result[2].sharedStageIds, ['86', '88', '24'])
})
test('相同属性的独立节点保持分开', () => {
  const result = build([branch('a', ['1']), branch('b', ['2'])], [stage('1'), stage('2')])
  assert.equal(result.some(s => s.shared), false)
  assert.deepEqual(result.map(s => s.stages[0].id), ['1', '2'])
})
test('部分分支共用时明确保留归属，忽略缺失阶段及重复引用', () => {
  const result = build([branch('a', ['1', '1', 'missing']), branch('b', ['1']), branch('c', ['2'])], [stage('1'), stage('2')])
  assert.deepEqual(result[0].branchIds, ['a', 'b'])
  assert.deepEqual(result.flatMap(s => s.stages.map(x => x.id)), ['1', '2'])
  assert.deepEqual(result[3].sharedStageIds, [])
})
test('单一分支顺序保持不变', () => {
  const result = build([branch('a', ['2', '1'])], [stage('1'), stage('2')])
  assert.deepEqual(result[0].stages.map(x => x.id), ['2', '1'])
  assert.deepEqual(build([], []), [])
})
