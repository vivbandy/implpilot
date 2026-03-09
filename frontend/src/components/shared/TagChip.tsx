import { cn } from '@/lib/utils'
import type { TagDefinition } from '@/types'

interface TagChipProps {
  tag: TagDefinition
  className?: string
}

// TagChip — Section 10.4:
// 11px medium text. Background is tag color at 15% opacity; text is full color.
// Fallback color when tag has no color defined: brand color.
export function TagChip({ tag, className }: TagChipProps) {
  const color = tag.color ?? '#0073EA'  // brand fallback
  const bgColor = hexToRgba(color, 0.15)

  return (
    <span
      className={cn(
        'inline-flex items-center px-1.5 py-0.5 rounded-sm text-xs font-medium whitespace-nowrap',
        className
      )}
      style={{
        backgroundColor: bgColor,
        color,
      }}
    >
      #{tag.name}
    </span>
  )
}

// Convert hex color to rgba for the 15% opacity background.
// Handles both #RGB and #RRGGBB formats.
function hexToRgba(hex: string, alpha: number): string {
  const clean = hex.replace('#', '')
  const expanded =
    clean.length === 3
      ? clean.split('').map((c) => c + c).join('')
      : clean

  const r = parseInt(expanded.substring(0, 2), 16)
  const g = parseInt(expanded.substring(2, 4), 16)
  const b = parseInt(expanded.substring(4, 6), 16)

  if (isNaN(r) || isNaN(g) || isNaN(b)) {
    return `rgba(0, 115, 234, ${alpha})`  // brand fallback
  }

  return `rgba(${r}, ${g}, ${b}, ${alpha})`
}
