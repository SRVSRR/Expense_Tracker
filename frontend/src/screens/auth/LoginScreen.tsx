import React, { useState } from 'react';
import { View, StyleSheet, KeyboardAvoidingView, Platform, ScrollView } from 'react-native';
import { TextInput, Button, Text, Surface } from 'react-native-paper';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Icon from '../../components/Icon';
import { Colors } from '../../theme/colors';
import { useAuthStore } from '../../store/authStore';

export default function LoginScreen({ navigation }: any) {
  const insets = useSafeAreaInsets();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const login = useAuthStore((state) => state.login);

  const handleLogin = async () => {
    if (!email || !password) {
      setError('Please fill in all fields');
      return;
    }
    setIsLoading(true);
    setError('');
    try {
      await login(email, password);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Login failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <ScrollView contentContainerStyle={[styles.scrollContent, { paddingTop: insets.top + 40 }]}>
        {/* Brand Header */}
        <View style={styles.brand}>
          <View style={styles.logoBg}>
            <Icon source="wallet" size={36} color="#fff" />
          </View>
          <Text variant="headlineMedium" style={styles.title}>
            Expense Tracker
          </Text>
          <Text variant="bodyMedium" style={styles.subtitle}>
            Take control of your finances
          </Text>
        </View>

        {/* Form Card */}
        <Surface style={styles.card} elevation={0}>
          <Text variant="titleMedium" style={styles.cardTitle}>
            Welcome back
          </Text>

          <TextInput
            label="Email"
            value={email}
            onChangeText={setEmail}
            mode="outlined"
            keyboardType="email-address"
            autoCapitalize="none"
            autoCorrect={false}
            left={<TextInput.Affix text="\u25AB" />}
            style={styles.input}
          />
          <TextInput
            label="Password"
            value={password}
            onChangeText={setPassword}
            mode="outlined"
            secureTextEntry={!showPassword}
            left={<TextInput.Affix text="\u25A1" />}
            right={
              <TextInput.Icon
                icon={() => (
                  <Icon source={showPassword ? 'eye-off' : 'eye'} size={18} color={Colors.textTertiary} />
                )}
                onPress={() => setShowPassword(!showPassword)}
              />
            }
            style={styles.input}
          />

          {error ? (
            <View style={styles.errorContainer}>
              <Icon source="alert-circle-outline" size={14} color={Colors.error} />
              <Text variant="bodySmall" style={styles.error}>
                {error}
              </Text>
            </View>
          ) : null}

          <Button
            mode="contained"
            onPress={handleLogin}
            loading={isLoading}
            disabled={isLoading}
            style={styles.button}
            buttonColor="#fff"
            textColor="#000"
            contentStyle={{ paddingVertical: 6 }}
          >
            Login
          </Button>

          <Button
            mode="text"
            onPress={() => navigation.navigate('Register')}
            style={styles.linkButton}
            textColor={Colors.primary}
          >
            Don't have an account? Sign up
          </Button>
        </Surface>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  scrollContent: {
    flexGrow: 1,
    justifyContent: 'center',
    padding: 24,
  },
  brand: {
    alignItems: 'center',
    marginBottom: 40,
  },
  logoBg: {
    width: 72,
    height: 72,
    borderRadius: 20,
    backgroundColor: Colors.primary,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
  },
  title: {
    fontWeight: '700',
    color: Colors.textPrimary,
    marginBottom: 4,
  },
  subtitle: {
    color: Colors.textSecondary,
  },
  card: {
    padding: 24,
    borderRadius: 16,
    backgroundColor: Colors.surfaceCard,
  },
  cardTitle: {
    fontWeight: '700',
    color: Colors.textPrimary,
    marginBottom: 20,
  },
  input: {
    marginBottom: 14,
    backgroundColor: Colors.surfaceElevated,
  },
  errorContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 12,
    padding: 10,
    backgroundColor: Colors.expenseSurface,
    borderRadius: 8,
  },
  error: {
    color: Colors.error,
    flex: 1,
  },
  button: {
    marginTop: 4,
    borderRadius: 10,
  },
  linkButton: {
    marginTop: 12,
  },
});
