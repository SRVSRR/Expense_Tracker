import React, { useEffect } from 'react';
import { StatusBar } from 'expo-status-bar';
import { PaperProvider, MD3DarkTheme } from 'react-native-paper';
import AppNavigator from './src/navigation/AppNavigator';
import { useAuthStore } from './src/store/authStore';
import { useNetworkSync } from './src/hooks/useNetworkSync';
import { Colors } from './src/theme/colors';

const theme = {
  ...MD3DarkTheme,
  colors: {
    ...MD3DarkTheme.colors,
    primary: Colors.primary,
    secondary: Colors.tertiary,
    error: Colors.error,
    background: Colors.background,
    surface: Colors.surface,
    surfaceVariant: Colors.surfaceCard,
    onBackground: Colors.textPrimary,
    onSurface: Colors.textPrimary,
    onSurfaceVariant: Colors.textSecondary,
    outline: Colors.border,
    outlineVariant: Colors.border,
  },
};

export default function App() {
  const loadToken = useAuthStore((state) => state.loadToken);
  useNetworkSync();

  useEffect(() => {
    loadToken();
  }, []);

  return (
    <PaperProvider theme={theme}>
      <AppNavigator />
      <StatusBar style="auto" />
    </PaperProvider>
  );
}
