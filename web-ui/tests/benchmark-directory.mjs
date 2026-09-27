/** 在相同日期格式化与测试数据下比较目录处理，排序单独测量。 */
import fs from 'node:fs'
import path from 'node:path'
import vm from 'node:vm'
import { createRequire } from 'node:module'
import ts from 'typescript'

const require = createRequire(import.meta.url)
const repository = path.resolve(process.argv[2] || '..')
const source = fs.readFileSync(path.join(repository, 'web-ui/src/utils/index.ts'), 'utf8')
const code = ts.transpileModule(source, { compilerOptions: {
  module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022, esModuleInterop: true,
}}).outputText
const context = vm.createContext({ exports: {}, require, URLSearchParams, window: { devicePixelRatio: 1 } })
vm.runInContext(code, context)
const api = context.exports
const median = values => [...values].sort((a, b) => a - b)[Math.floor(values.length / 2)]
for (const paired of [false, true]) {
  for (const count of [1000, 2000, 5000]) {
    const timings = [], sorting = []
    for (let repeat = 0; repeat < 5; repeat++) {
      const files = Array.from({ length: count }, (_, i) => ({ name: `image_${i}.png`, type: 'file',
        created_at: 1700000000 + i, bytes: 1024, folder_path: 'fixture', file_version: '1:1024', index_generation: 1 }))
      if (paired) files.push(...Array.from({ length: count }, (_, i) => ({ name: `image_${i}.json`, type: 'file',
        created_at: 1700000000 + i, bytes: 100, folder_path: 'fixture' })))
      let started = performance.now()
      const result = api.processDirectoryFiles
        ? api.processDirectoryFiles(files, 'outputs', 'fixture')
        : files.map(file => api.processFileInfo(file, 'outputs', files)).filter(Boolean)
      timings.push(performance.now() - started)
      started = performance.now()
      result.sort((a, b) => b.created_at - a.created_at)
      sorting.push(performance.now() - started)
    }
    console.log(JSON.stringify({ images: count, paired, repeats: 5,
      processing_ms: Number(median(timings).toFixed(3)), sorting_ms: Number(median(sorting).toFixed(3)) }))
  }
}
