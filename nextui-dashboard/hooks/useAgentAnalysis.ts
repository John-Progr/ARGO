import { useState, useCallback, useEffect } from 'react'

export interface AgentScore {
  score: number
  reason: string
}

export interface TradeParams {
  entry_range: string
  stop_loss: string
  take_profit_1: string
  take_profit_2: string
  position_size: {
    conservative: string
    medium: string
    aggressive: string
  }
}

export interface AnalysisVerdict {
  approved: boolean
  overall_confidence: number
  final_recommendation: 'BUY' | 'SELL' | 'HOLD' | 'INSUFFICIENT DATA'
  recommendation_confidence: 'LOW' | 'MEDIUM' | 'HIGH'
  scores: {
    news: AgentScore
    onchain: AgentScore
    technical: AgentScore
    macro: AgentScore
    risk: AgentScore
  }
  trade_parameters: TradeParams
  invalidation_conditions: string[]
  reason: string
  failed_agents: string[]
}

// Includes FinalVersion's approval flow statuses
export type JobPhase =
  | 'queued'
  | 'running'
  | 'awaiting_approval'   // BUY/SELL verdict ready, waiting for human sign-off
  | 'generating_script'  // approved → Move script being generated
  | 'done'
  | 'rejected'
  | 'error'

export interface JobStatus {
  status: JobPhase
  coin: string
  amount_usd: number
  fidelity: string
  result: AnalysisVerdict | { error: string } | null
  move_script?: string
}

const TERMINAL_PHASES = new Set<JobPhase>(['done', 'rejected', 'error'])

export function useAgentAnalysis() {
  const [jobId, setJobId] = useState<string | null>(null)
  const [job, setJob] = useState<JobStatus | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Poll while the job is in-flight (including awaiting_approval + generating_script)
  useEffect(() => {
    if (!jobId || (job?.status && TERMINAL_PHASES.has(job.status))) return
    const id = setInterval(async () => {
      try {
        const res = await fetch(`/api/result/${jobId}`)
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        const data: JobStatus = await res.json()
        setJob(data)
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Poll failed')
      }
    }, 3000)
    return () => clearInterval(id)
  }, [jobId, job?.status])

  const analyze = useCallback(async (amount_usd: number, fidelity: 'LOW' | 'HIGH') => {
    setSubmitting(true)
    setError(null)
    setJob(null)
    setJobId(null)
    try {
      const res = await fetch('/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ amount_usd, fidelity }),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      if (data.error) throw new Error(data.error)
      setJobId(data.job_id)
      setJob({ status: 'queued', coin: 'SUI', amount_usd, fidelity, result: null })
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to start analysis')
    } finally {
      setSubmitting(false)
    }
  }, [])

  const approve = useCallback(async () => {
    if (!jobId) return
    try {
      const res = await fetch(`/api/approve/${jobId}`, { method: 'POST' })
      const data = await res.json()
      if (data.error) throw new Error(data.error)
      setJob(prev => prev ? { ...prev, status: 'generating_script' } : prev)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Approval failed')
    }
  }, [jobId])

  const reject = useCallback(async () => {
    if (!jobId) return
    try {
      const res = await fetch(`/api/reject/${jobId}`, { method: 'POST' })
      const data = await res.json()
      if (data.error) throw new Error(data.error)
      setJob(prev => prev ? { ...prev, status: 'rejected' } : prev)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Rejection failed')
    }
  }, [jobId])

  const verdict =
    job?.result && !('error' in job.result)
      ? (job.result as AnalysisVerdict)
      : null

  return { job, jobId, submitting, error, analyze, approve, reject, verdict }
}
