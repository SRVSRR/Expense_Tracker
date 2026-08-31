import React from 'react';
import { Text, TextStyle } from 'react-native';

const glyphMap: Record<string, string> = {
  'home': '\u2302',
  'home-outline': '\u2302',
  'format-list-bulleted': '\u2022',
  'plus-circle': '\u2795',
  'plus-circle-outline': '\u2795',
  'wallet': '\u25A3',
  'wallet-outline': '\u25A1',
  'trending-up': '\u25B2',
  'chart-pie': '\u25D4',
  'chart-bar': '\u2587',
  'clock-outline': '\u23F0',
  'alert-circle-outline': '\u26A0',
  'chevron-down': '\u25BC',
  'arrow-down-bold': '\u2B07',
  'arrow-up-bold': '\u2B06',
  'currency-usd': '$',
  'clock': '\u23F0',
  'warning': '\u26A0',
};

interface IconProps {
  source: string;
  size?: number;
  color?: string;
}

export default function Icon({ source, size = 24, color = '#000' }: IconProps) {
  const glyph = glyphMap[source] || '\u2022';
  return (
    <Text
      style={{
        fontSize: size,
        color,
        lineHeight: size * 1.2,
      } as TextStyle}
    >
      {glyph}
    </Text>
  );
}
