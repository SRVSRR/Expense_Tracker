import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { useAuthStore } from '../store/authStore';
import { ActivityIndicator, View } from 'react-native';
import Icon from '../components/Icon';

import LoginScreen from '../screens/auth/LoginScreen';
import RegisterScreen from '../screens/auth/RegisterScreen';
import DashboardScreen from '../screens/main/DashboardScreen';
import TransactionsScreen from '../screens/main/TransactionsScreen';
import AddTransactionScreen from '../screens/main/AddTransactionScreen';
import AccountsScreen from '../screens/main/AccountsScreen';
import ForecastScreen from '../screens/main/ForecastScreen';
import BudgetScreen from '../screens/main/BudgetScreen';

const Stack = createNativeStackNavigator();
const Tab = createBottomTabNavigator();

const AuthStack = () => (
  <Stack.Navigator
    screenOptions={{
      headerShown: false,
      contentStyle: { backgroundColor: '#F5F5F5' },
    }}
  >
    <Stack.Screen name="Login" component={LoginScreen} />
    <Stack.Screen name="Register" component={RegisterScreen} />
  </Stack.Navigator>
);

const iconMap: Record<string, { focused: string; unfocused: string }> = {
  Home: { focused: 'home', unfocused: 'home-outline' },
  Transactions: { focused: 'format-list-bulleted', unfocused: 'format-list-bulleted' },
  AddTxn: { focused: 'plus-circle', unfocused: 'plus-circle-outline' },
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
        return <Icon source={focused ? icons.focused : icons.unfocused} size={size} color={color} />;
      },
      tabBarActiveTintColor: '#2196F3',
      tabBarInactiveTintColor: '#999',
      tabBarStyle: {
        backgroundColor: '#fff',
        borderTopColor: '#E0E0E0',
        paddingBottom: 4,
        paddingTop: 4,
        height: 56,
      },
      tabBarLabelStyle: {
        fontSize: 10,
        fontWeight: '600' as const,
        flexShrink: 0,
      },
    })}
  >
    <Tab.Screen name="Home" component={DashboardScreen} options={{ tabBarLabel: 'Home' }} />
    <Tab.Screen name="Transactions" component={TransactionsScreen} />
    <Tab.Screen
      name="AddTxn"
      component={AddTransactionScreen}
      options={{ tabBarLabel: 'Add' }}
    />
    <Tab.Screen name="Accounts" component={AccountsScreen} />
    <Tab.Screen name="Forecast" component={ForecastScreen} />
    <Tab.Screen name="Budget" component={BudgetScreen} />
  </Tab.Navigator>
);

export default function AppNavigator() {
  const { isAuthenticated, isLoading } = useAuthStore();

  if (isLoading) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#F5F5F5' }}>
        <ActivityIndicator size="large" color="#2196F3" />
      </View>
    );
  }

  return (
    <NavigationContainer>
      {isAuthenticated ? <MainTabs /> : <AuthStack />}
    </NavigationContainer>
  );
}
