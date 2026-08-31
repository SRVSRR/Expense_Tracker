import React from 'react';
import { Text, TextStyle } from 'react-native';

const glyphMap: Record<string, string> = {
  'home': '\u2302',
  'home-outline': '\u2302',
  'format-list-bulleted': '\u2630',
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
  'chevron-right': '\u25B6',
  'arrow-down-bold': '\u2B07',
  'arrow-up-bold': '\u2B06',
  'currency-usd': '$',
  'clock': '\u23F0',
  'warning': '\u26A0',
  'check': '\u2714',
  'check-circle': '\u2714',
  'close': '\u2716',
  'delete': '\u2718',
  'edit': '\u270E',
  'search': '\u1F50D',
  'calendar': '\u1F4C5',
  'tag': '\u25B7',
  'repeat': '\u27F3',
  'account': '\u263A',
  'account-outline': '\u263A',
  'lock': '\u26BF',
  'email': '\u2709',
  'eye': '\u25C9',
  'eye-off': '\u25CB',
  'arrow-left': '\u25C0',
  'menu': '\u2630',
  'filter': '\u2699',
  'info': '\u2139',
  'help-circle': '\u2753',
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
        textAlign: 'center',
      } as TextStyle}
    >
      {glyph}
    </Text>
  );
}
