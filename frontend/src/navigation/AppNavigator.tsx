import React from 'react';
import { View, StyleSheet } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { useAuthStore } from '../store/authStore';
import { ActivityIndicator } from 'react-native';
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
        if (route.name === 'AddTxn') {
          return (
            <View style={styles.addIconContainer}>
              <Icon source={focused ? icons.focused : icons.unfocused} size={24} color="#fff" />
            </View>
          );
        }
        return <Icon source={focused ? icons.focused : icons.unfocused} size={size} color={color} />;
      },
      tabBarActiveTintColor: '#2196F3',
      tabBarInactiveTintColor: '#999',
      tabBarStyle: styles.tabBar,
      tabBarLabelStyle: styles.tabLabel,
      tabBarHideOnKeyboard: true,
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
      <View style={styles.loading}>
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

const styles = StyleSheet.create({
  tabBar: {
    backgroundColor: '#fff',
    borderTopColor: '#E8E8E8',
    borderTopWidth: 0.5,
    paddingBottom: 6,
    paddingTop: 6,
    height: 58,
    elevation: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: -2 },
    shadowOpacity: 0.06,
    shadowRadius: 8,
  },
  tabLabel: {
    fontSize: 10,
    fontWeight: '600' as const,
    flexShrink: 0,
    marginTop: -2,
  },
  addIconContainer: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: '#2196F3',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
    elevation: 4,
    shadowColor: '#2196F3',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
  },
  loading: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#F5F5F5',
  },
});
