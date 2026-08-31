import React from 'react';
import { Text, TextStyle } from 'react-native';

const glyphMap: Record<string, string> = {
  'home': '\u2302',
  'home-outline': '\u2302',
  'format-list-bulleted': '\u2261',
  'plus-circle': '\u002B',
  'plus-circle-outline': '\u002B',
  'wallet': '\u25A7',
  'wallet-outline': '\u25A1',
  'trending-up': '\u25B3',
  'chart-pie': '\u25D3',
  'chart-bar': '\u2587',
  'clock-outline': '\u29D6',
  'alert-circle-outline': '\u26A0',
  'chevron-down': '\u25BE',
  'chevron-right': '\u25B8',
  'arrow-down-bold': '\u2193',
  'arrow-up-bold': '\u2191',
  'currency-usd': '\u0024',
  'clock': '\u29D6',
  'warning': '\u26A0',
  'check': '\u2713',
  'check-circle': '\u2713',
  'close': '\u2715',
  'delete': '\u2715',
  'info': '\u2139',
  'repeat': '\u21BB',
  'tag': '\u25B8',
  'account': '\u263A',
  'account-outline': '\u263A',
  'lock': '\u26BF',
  'email': '\u2709',
  'eye': '\u25CE',
  'eye-off': '\u25CB',
  'arrow-left': '\u25C0',
  'menu': '\u2261',
  'filter': '\u2261',
  'help-circle': '\u2370',
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
