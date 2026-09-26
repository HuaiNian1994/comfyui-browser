import type { MetadataBranch, MetadataStage } from '@/types'

export interface MetadataSection {
  id: string
  shared: boolean
  branchIds: string[]
  stages: MetadataStage[]
  sharedStageIds: string[]
}

/** 按同一执行图节点的分支归属合并展示，值相同的独立节点仍分别保留。 */
export function buildMetadataSections(branches: MetadataBranch[], stages: MetadataStage[]): MetadataSection[] {
  const owners = new Map<string, string[]>()
  for (const branch of branches) {
    for (const id of new Set(branch.stage_ids)) owners.set(id, [...(owners.get(id) || []), branch.id])
  }
  const shared = new Map<string, MetadataSection>()
  for (const stage of stages) {
    const branchIds = owners.get(stage.id) || []
    if (branchIds.length < 2) continue
    const key = JSON.stringify(branchIds)
    if (!shared.has(key)) shared.set(key, { id: `shared-${key}`, shared: true, branchIds, stages: [], sharedStageIds: [] })
    shared.get(key)!.stages.push(stage)
  }
  const byId = new Map(stages.map(stage => [stage.id, stage]))
  return [...shared.values(), ...branches.map(branch => ({
    id: branch.id, shared: false, branchIds: [branch.id],
    stages: [...new Set(branch.stage_ids)].filter(id => owners.get(id)?.length === 1).map(id => byId.get(id)).filter((stage): stage is MetadataStage => !!stage),
    sharedStageIds: [...new Set(branch.stage_ids)].filter(id => (owners.get(id)?.length || 0) > 1 && byId.has(id)),
  }))]
}
