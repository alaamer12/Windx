/**
 * Color utility functions for consistent color handling across the application
 * Following Single Responsibility Principle for better reusability
 */

// Professional Color Palette - Comprehensive color mapping
const COLOR_PALETTE: Record<string, string> = {
  // Whites / Off-whites
  'white': '#F8FAFC',
  'snow': '#FFFAFA',
  'ivory': '#FFFFF0',
  'cream': '#FFFDD0',
  'beige': '#F5F5DC',
  'silver': '#C0C0C0',
  
  // Grays / Blacks
  'black': '#1a1a1a',
  'gray': '#6B7280',
  'grey': '#6B7280',
  'slate': '#475569',
  'charcoal': '#36454F',
  
  // Reds / Pinks
  'red': '#EF4444',
  'rose': '#F43F5E',
  'crimson': '#DC143C',
  'maroon': '#800000',
  'pink': '#EC4899',
  'fuchsia': '#D946EF',
  
  // Oranges / Yellows
  'orange': '#F97316',
  'amber': '#F59E0B',
  'yellow': '#EAB308',
  'gold': '#FFD700',
  'bronze': '#CD7F32',
  'brown': '#92400E',
  
  // Greens
  'green': '#22C55E',
  'emerald': '#10B981',
  'lime': '#84CC16',
  'olive': '#808000',
  'teal': '#14B8A6',
  
  // Blues
  'blue': '#3B82F6',
  'navy': '#000080',
  'sky': '#0EA5E9',
  'cyan': '#06B6D4',
  'indigo': '#6366F1',
  'royal': '#4169E1',
  
  // Purples
  'purple': '#A855F7',
  'violet': '#8B5CF6',
  'magenta': '#FF00FF',
}

/**
 * Get hex color value from color name
 * @param colorName - The name of the color (case-insensitive)
 * @returns Hex color string (e.g., '#F8FAFC')
 */
export function getColorHex(colorName: string): string {
  if (!colorName) return '#E2E8F0' // Default gray
  
  const name = String(colorName).toLowerCase().trim()
  
  // 1. Exact match
  if (COLOR_PALETTE[name]) {
    return COLOR_PALETTE[name]
  }
  
  // 2. Fuzzy match - find colors that contain the search term
  const matches = Object.keys(COLOR_PALETTE).filter(key => 
    name.includes(key) || key.includes(name)
  )
  
  if (matches.length > 0) {
    // Sort by length (longer matches are more specific)
    const sorted = matches.sort((a, b) => b.length - a.length)
    const bestMatch = sorted[0]
    if (bestMatch && COLOR_PALETTE[bestMatch]) {
      return COLOR_PALETTE[bestMatch]
    }
  }
  
  // 3. Fallback: Generate color from string hash
  return generateColorFromString(name)
}

/**
 * Generate a consistent color from a string using hash
 * @param str - Input string
 * @returns Hex color string
 */
export function generateColorFromString(str: string): string {
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash)
  }
  const c = (hash & 0x00ffffff).toString(16).toUpperCase()
  return '#' + '00000'.substring(0, 6 - c.length) + c
}

/**
 * Calculate contrast text color (black or white) for a given background color
 * @param hexColor - Background color in hex format
 * @returns '#1F2937' (dark) or '#FFFFFF' (white)
 */
export function getContrastTextColor(hexColor: string): string {
  const hex = hexColor.replace('#', '')
  const r = parseInt(hex.substring(0, 2), 16)
  const g = parseInt(hex.substring(2, 4), 16)
  const b = parseInt(hex.substring(4, 6), 16)
  
  // Calculate relative luminance using WCAG formula
  const uicolors = [r / 255, g / 255, b / 255]
  const c = uicolors.map((col) => {
    if (col <= 0.03928) {
      return col / 12.92
    }
    return Math.pow((col + 0.055) / 1.055, 2.4)
  })
  
  const rL = c[0] ?? 0
  const gL = c[1] ?? 0
  const bL = c[2] ?? 0
  
  const L = 0.2126 * rL + 0.7152 * gL + 0.0722 * bL
  
  // Return dark text for light backgrounds, white text for dark backgrounds
  return L > 0.4 ? '#1F2937' : '#FFFFFF'
}

/**
 * Get appropriate border color for a background color
 * @param hexColor - Background color in hex format
 * @returns Border color (light gray or transparent)
 */
export function getBorderColor(hexColor: string): string {
  return getContrastTextColor(hexColor) === '#1F2937' ? '#E2E8F0' : 'transparent'
}

/**
 * Get complete color style object for UI components
 * @param colorName - The name of the color
 * @returns Object with backgroundColor, color, and borderColor
 */
export function getColorStyle(colorName: string): {
  backgroundColor: string
  color: string
  borderColor: string
} {
  const bgColor = getColorHex(colorName)
  return {
    backgroundColor: bgColor,
    color: getContrastTextColor(bgColor),
    borderColor: getBorderColor(bgColor)
  }
}

/**
 * Check if a color name exists in the palette
 * @param colorName - The name of the color to check
 * @returns True if color exists in palette
 */
export function isKnownColor(colorName: string): boolean {
  if (!colorName) return false
  const name = String(colorName).toLowerCase().trim()
  return COLOR_PALETTE.hasOwnProperty(name)
}

/**
 * Get all available color names from the palette
 * @returns Array of color names
 */
export function getAvailableColors(): string[] {
  return Object.keys(COLOR_PALETTE)
}

/**
 * Get color information for display purposes
 * @param colorName - The name of the color
 * @returns Object with name, hex, and style information
 */
export function getColorInfo(colorName: string): {
  name: string
  hex: string
  style: ReturnType<typeof getColorStyle>
  isKnown: boolean
} {
  const hex = getColorHex(colorName)
  return {
    name: colorName,
    hex,
    style: getColorStyle(colorName),
    isKnown: isKnownColor(colorName)
  }
}

/**
 * Validate if a string is a valid hex color
 * @param hex - Hex color string to validate
 * @returns True if valid hex color
 */
export function isValidHexColor(hex: string): boolean {
  return /^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$/.test(hex)
}

/**
 * Convert RGB values to hex color
 * @param r - Red value (0-255)
 * @param g - Green value (0-255)
 * @param b - Blue value (0-255)
 * @returns Hex color string
 */
export function rgbToHex(r: number, g: number, b: number): string {
  const toHex = (n: number) => {
    const hex = Math.round(Math.max(0, Math.min(255, n))).toString(16)
    return hex.length === 1 ? '0' + hex : hex
  }
  return `#${toHex(r)}${toHex(g)}${toHex(b)}`
}

/**
 * Convert hex color to RGB values
 * @param hex - Hex color string
 * @returns Object with r, g, b values
 */
export function hexToRgb(hex: string): { r: number; g: number; b: number } | null {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex)
  return result && result[1] && result[2] && result[3] ? {
    r: parseInt(result[1], 16),
    g: parseInt(result[2], 16),
    b: parseInt(result[3], 16)
  } : null
}