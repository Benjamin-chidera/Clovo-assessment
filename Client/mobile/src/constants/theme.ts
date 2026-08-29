/**
 * Below are the colors that are used in the app. The colors are defined in the light and dark mode.
 * There are many other ways to style your app. For example, [Nativewind](https://www.nativewind.dev/), [Tamagui](https://tamagui.dev/), [unistyles](https://reactnativeunistyles.vercel.app), etc.
 */

import { Platform } from 'react-native';

export const ClovoColors = {
  primary: '#3B49DF',
  primaryDark: '#2B38C6',
  primaryLight: '#EEF2FF',
  streak: '#FF6B00',
  streakSecondary: '#F97316',
  surfaceBackground: '#F8F9FD',
  cardBackground: '#FFFFFF',
  darkCard: '#1C1C1E',
  darkCardTexture: '#2C2C2E',
  textPrimary: '#111827',
  textSecondary: '#6B7280',
  textMuted: '#9CA3AF',
  textOnPrimary: '#FFFFFF',
  online: '#10B981',
  onlineLight: '#D1FAE5',
  border: '#E5E7EB',
  borderLight: '#F3F4F6',
  shadowColor: 'rgba(0, 0, 0, 0.06)',
} as const;

export const Colors = {
  light: {
    text: '#111827',
    background: '#F8F9FD',
    backgroundElement: '#EEF2FF',
    backgroundSelected: '#E0E7FF',
    textSecondary: '#6B7280',
    primary: ClovoColors.primary,
    card: ClovoColors.cardBackground,
    border: ClovoColors.border,
  },
  dark: {
    text: '#F9FAFB',
    background: '#111827',
    backgroundElement: '#1F2937',
    backgroundSelected: '#374151',
    textSecondary: '#9CA3AF',
    primary: ClovoColors.primary,
    card: ClovoColors.darkCard,
    border: '#374151',
  },
} as const;

export type ThemeColor = keyof typeof Colors.light & keyof typeof Colors.dark;

export const Fonts = Platform.select({
  ios: {
    /** iOS `UIFontDescriptorSystemDesignDefault` */
    sans: 'system-ui',
    /** iOS `UIFontDescriptorSystemDesignSerif` */
    serif: 'ui-serif',
    /** iOS `UIFontDescriptorSystemDesignRounded` */
    rounded: 'ui-rounded',
    /** iOS `UIFontDescriptorSystemDesignMonospaced` */
    mono: 'ui-monospace',
  },
  default: {
    sans: 'normal',
    serif: 'serif',
    rounded: 'normal',
    mono: 'monospace',
  },
  web: {
    sans: 'var(--font-display)',
    serif: 'var(--font-serif)',
    rounded: 'var(--font-rounded)',
    mono: 'var(--font-mono)',
  },
});

export const Spacing = {
  half: 2,
  one: 4,
  two: 8,
  three: 16,
  four: 24,
  five: 32,
  six: 64,
} as const;

export const BottomTabInset = Platform.select({ ios: 50, android: 80 }) ?? 0;
export const MaxContentWidth = 800;
