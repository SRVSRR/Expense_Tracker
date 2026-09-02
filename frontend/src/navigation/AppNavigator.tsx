import React from 'react';
import { View, StyleSheet } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { useAuthStore } from '../store/authStore';
import { ActivityIndicator } from 'react-native';
import Icon from '../components/Icon';
import { Colors } from '../theme/colors';

import LoginScreen from '../screens/auth/LoginScreen';
import RegisterScreen from '../screens/auth/RegisterScreen';
import DashboardScreen from '../screens/main/DashboardScreen';
import TransactionsScreen from '../screens/main/TransactionsScreen';
import AddTransactionScreen from '../screens/main/AddTransactionScreen';
import AddAccountScreen from '../screens/main/AddAccountScreen';
import AccountsScreen from '../screens/main/AccountsScreen';
import ForecastScreen from '../screens/main/ForecastScreen';
import BudgetScreen from '../screens/main/BudgetScreen';

const Stack = createNativeStackNavigator();
const Tab = createBottomTabNavigator();

const AuthStack = () => (
  <Stack.Navigator
    screenOptions={{
      headerShown: false,
      contentStyle: { backgroundColor: Colors.background },
    }}
  >
    <Stack.Screen name="Login" component={LoginScreen} />
    <Stack.Screen name="Register" component={RegisterScreen} />
  </Stack.Navigator>
);

const iconMap: Record<string, { focused: string; unfocused: string }> = {
  Home: { focused: 'home', unfocused: 'home-outline' },
  Transactions: { focused: 'format-list-bulleted', unfocused: 'format-list-bulleted' },
  Accounts: { focused: 'wallet', unfocused: 'wallet-outline' },
  Forecast: { focused: 'trending-up', unfocused: 'trending-up' },
  Budget: { focused: 'chart-pie', unfocused: 'chart-pie' },
};

const MainTabs = () => (
  <Tab.Navigator
    screenOptions={({ route }) => ({
      headerShown: false,
      tabBarIcon: ({ focused, color, size }) => {
        const icons = iconMap[route.name] || { focused: 'home', unfocused: 'home-outline' };
        return <Icon source={focused ? icons.focused : icons.unfocused} size={20} color={color} />;
      },
      tabBarActiveTintColor: Colors.textPrimary,
      tabBarInactiveTintColor: Colors.textTertiary,
      tabBarStyle: styles.tabBar,
      tabBarLabelStyle: styles.tabLabel,
      tabBarHideOnKeyboard: true,
    })}
  >
    <Tab.Screen name="Home" component={DashboardScreen} />
    <Tab.Screen name="Transactions" component={TransactionsScreen} />
    <Tab.Screen name="Accounts" component={AccountsScreen} />
    <Tab.Screen name="Forecast" component={ForecastScreen} />
    <Tab.Screen name="Budget" component={BudgetScreen} />
  </Tab.Navigator>
);

const RootStack = () => {
  const { isAuthenticated, isLoading } = useAuthStore();

  if (isLoading) {
    return (
      <View style={styles.loading}>
        <ActivityIndicator size="large" color={Colors.primary} />
      </View>
    );
  }

  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      {isAuthenticated ? (
        <>
          <Stack.Screen name="MainTabs" component={MainTabs} />
          <Stack.Screen
            name="AddTransaction"
            component={AddTransactionScreen}
            options={{ presentation: 'modal' }}
          />
          <Stack.Screen
            name="AddAccount"
            component={AddAccountScreen}
            options={{ presentation: 'modal' }}
          />
        </>
      ) : (
        <Stack.Screen name="Auth" component={AuthStack} />
      )}
    </Stack.Navigator>
  );
};

export default function AppNavigator() {
  return (
    <NavigationContainer>
      <RootStack />
    </NavigationContainer>
  );
}

const styles = StyleSheet.create({
  tabBar: {
    backgroundColor: Colors.surface,
    borderTopColor: Colors.border,
    borderTopWidth: 0.5,
    paddingBottom: 4,
    paddingTop: 4,
    height: 52,
    elevation: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: -2 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
  },
  tabLabel: {
    fontSize: 9,
    fontWeight: '600' as const,
    marginTop: -1,
  },
  loading: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: Colors.background,
  },
});
