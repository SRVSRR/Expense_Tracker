import React, { useState } from 'react';
import { View, StyleSheet, KeyboardAvoidingView, Platform, ScrollView } from 'react-native';
import { TextInput, Button, Text, Surface } from 'react-native-paper';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Icon from '../../components/Icon';
import { useAuthStore } from '../../store/authStore';

export default function RegisterScreen({ navigation }: any) {
  const insets = useSafeAreaInsets();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const register = useAuthStore((state) => state.register);

  const handleRegister = async () => {
    if (!email || !password || !confirmPassword) {
      setError('Please fill in all fields');
      return;
    }
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    if (password.length < 6) {
      setError('Password must be at least 6 characters');
      return;
    }
    setIsLoading(true);
    setError('');
    try {
      await register(email, password);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Registration failed. Please try again.');
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
            Get Started
          </Text>
          <Text variant="bodyMedium" style={styles.subtitle}>
            Create your account to begin tracking
          </Text>
        </View>

        {/* Form Card */}
        <Surface style={styles.card} elevation={2}>
          <TextInput
            label="Email"
            value={email}
            onChangeText={setEmail}
            mode="outlined"
            keyboardType="email-address"
            autoCapitalize="none"
            autoCorrect={false}
            left={<TextInput.Affix text="\u2709" />}
            style={styles.input}
          />
          <TextInput
            label="Password"
            value={password}
            onChangeText={setPassword}
            mode="outlined"
            secureTextEntry={!showPassword}
            left={<TextInput.Affix text="\u26BF" />}
            right={
              <TextInput.Icon
                icon={() => (
                  <Icon source={showPassword ? 'eye-off' : 'eye'} size={18} color="#999" />
                )}
                onPress={() => setShowPassword(!showPassword)}
              />
            }
            style={styles.input}
          />
          <TextInput
            label="Confirm Password"
            value={confirmPassword}
            onChangeText={setConfirmPassword}
            mode="outlined"
            secureTextEntry={!showPassword}
            left={<TextInput.Affix text="\u26BF" />}
            style={styles.input}
          />

          {error ? (
            <View style={styles.errorContainer}>
              <Icon source="alert-circle-outline" size={14} color="#F44336" />
              <Text variant="bodySmall" style={styles.error}>
                {error}
              </Text>
            </View>
          ) : null}

          <Button
            mode="contained"
            onPress={handleRegister}
            loading={isLoading}
            disabled={isLoading}
            style={styles.button}
            buttonColor="#2196F3"
            contentStyle={{ paddingVertical: 6 }}
          >
            Create Account
          </Button>

          <Button
            mode="text"
            onPress={() => navigation.navigate('Login')}
            style={styles.linkButton}
            textColor="#2196F3"
          >
            Already have an account? Log in
          </Button>
        </Surface>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F5',
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
    backgroundColor: '#2196F3',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
  },
  title: {
    fontWeight: '700',
    color: '#333',
    marginBottom: 4,
  },
  subtitle: {
    color: '#999',
  },
  card: {
    padding: 24,
    borderRadius: 16,
    backgroundColor: '#fff',
  },
  input: {
    marginBottom: 14,
    backgroundColor: '#FAFAFA',
  },
  errorContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 12,
    padding: 10,
    backgroundColor: '#FFF5F5',
    borderRadius: 8,
  },
  error: {
    color: '#F44336',
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
