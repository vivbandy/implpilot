import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

// cn() is the shadcn/ui standard helper: combines clsx conditional
// class logic with tailwind-merge deduplication.
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
