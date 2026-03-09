import { cn } from '@/lib/utils'

interface HealthSpectrumBarProps {
  score: number       // 0–100
  size?: 'sm' | 'md'
  showLabel?: boolean
  showScore?: boolean
  className?: string
}

// HealthSpectrumBar — Section 5.2:
// Horizontal gradient bar — no hard threshold lines, smooth gradient.
// The marker (|) sits at the score position on the gradient.
//
// Color mapping:
//   0–39:   #EF4444 → #F97316
//   40–69:  #F97316 → #EAB308
//   70–100: #EAB308 → #22C55E
//
// Semantic labels:
//   0–39:   "At Risk"
//   40–59:  "Needs Attention"
//   60–74:  "On Track"
//   75–100: "Healthy"
export function HealthSpectrumBar({
  score,
  size = 'md',
  showLabel = false,
  showScore = false,
  className,
}: HealthSpectrumBarProps) {
  const clampedScore = Math.min(100, Math.max(0, score))
  const markerPct = `${clampedScore}%`
  const label = getHealthLabel(clampedScore)

  return (
    <div className={cn('w-full', className)}>
      {(showLabel || showScore) && (
        <div className="flex items-center justify-between mb-1">
          {showLabel && (
            <span className="text-xs font-medium" style={{ color: getHealthColor(clampedScore) }}>
              {label}
            </span>
          )}
          {showScore && (
            <span className="text-xs text-text-secondary ml-auto">
              {clampedScore}/100
            </span>
          )}
        </div>
      )}

      {/* Gradient track */}
      <div
        className={cn(
          'relative w-full rounded-pill overflow-visible',
          size === 'sm' ? 'h-1.5' : 'h-2.5'
        )}
        style={{
          // Full red→orange→yellow→green gradient spanning the entire bar
          background: 'linear-gradient(to right, #EF4444 0%, #F97316 30%, #EAB308 60%, #22C55E 100%)',
        }}
      >
        {/* Score marker — thin white tick at the score position */}
        <div
          className="absolute top-1/2 -translate-y-1/2 w-0.5 bg-white rounded-full shadow-sm"
          style={{
            left: markerPct,
            height: size === 'sm' ? '10px' : '14px',
            // Keep marker from overflowing the bar ends
            transform: `translateX(-50%) translateY(-50%)`,
          }}
        />
      </div>
    </div>
  )
}

function getHealthLabel(score: number): string {
  if (score < 40) return 'At Risk'
  if (score < 60) return 'Needs Attention'
  if (score < 75) return 'On Track'
  return 'Healthy'
}

// Returns the point color at this score position on the gradient.
// Used for the semantic label text color.
function getHealthColor(score: number): string {
  if (score < 40) return '#EF4444'
  if (score < 60) return '#F97316'
  if (score < 75) return '#EAB308'
  return '#22C55E'
}
