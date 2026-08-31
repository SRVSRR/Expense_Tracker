import React, { useEffect } from 'react';
import { StatusBar } from 'expo-status-bar';
import { PaperProvider, MD3LightTheme } from 'react-native-paper';
import AppNavigator from './src/navigation/AppNavigator';
import { useAuthStore } from './src/store/authStore';
import { useNetworkSync } from './src/hooks/useNetworkSync';

const theme = {
  ...MD3LightTheme,
  colors: {
    ...MD3LightTheme.colors,
    primary: '#2196F3',
    secondary: '#4CAF50',
    error: '#F44336',
    background: '#F5F5F5',
    surface: '#FFFFFF',
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
