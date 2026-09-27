import type { GenerationTiming } from '@/types'

/** 时间按原始值选择单位；向下保留两位避免 59.999 秒显示成 60 秒。 */
export function formatDuration(milliseconds: number, secondsUnit: string, minutesUnit: string): string {
  const value = milliseconds < 60000 ? milliseconds / 1000 : milliseconds / 60000
  const unit = milliseconds < 60000 ? secondsUnit : minutesUnit
  return `${value > 0 && value < 0.01 ? '<0.01' : String(Math.floor(value * 100 + 1e-9) / 100)} ${unit}`
}

export function timingValues(timing?: GenerationTiming): Array<{ id: string; value: number }> {
  if (!timing || !Number.isFinite(timing.total_ms) || timing.total_ms < 0) return []
  const result = [{ id: 'total', value: timing.total_ms }]
  if (typeof timing.sampling_ms === 'number' && Number.isFinite(timing.sampling_ms) && timing.sampling_ms > 0) {
    result.push({ id: 'sampling', value: timing.sampling_ms })
    if (Number.isInteger(timing.iterations) && timing.iterations! > 0) result.push({ id: 'average', value: timing.sampling_ms / timing.iterations! })
  }
  return result
}
