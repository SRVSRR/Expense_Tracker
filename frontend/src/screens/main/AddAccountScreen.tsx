import React, { useState } from 'react';
import { View, StyleSheet, ScrollView, Alert, KeyboardAvoidingView, Platform } from 'react-native';
import { TextInput, Button, Text, Surface } from 'react-native-paper';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Icon from '../../components/Icon';
import { Colors } from '../../theme/colors';
import { useAccountStore } from '../../store/accountStore';

export default function AddAccountScreen({ navigation }: any) {
  const insets = useSafeAreaInsets();
  const { createAccount } = useAccountStore();
  const [name, setName] = useState('');
  const [currency, setCurrency] = useState('USD');
  const [balance, setBalance] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleCreate = async () => {
    if (!name.trim()) {
      Alert.alert('Error', 'Please enter an account name');
      return;
    }
    const parsed = parseFloat(balance);
    if (isNaN(parsed) || parsed < 0) {
      Alert.alert('Error', 'Please enter a valid balance');
      return;
    }
    setIsLoading(true);
    try {
      await createAccount({
        name: name.trim(),
        currency,
        initial_balance: parsed,
      });
      navigation.goBack();
    } catch (error: any) {
      const detail = error?.response?.data?.detail || error?.message || 'Failed to create account';
      Alert.alert('Error', typeof detail === 'string' ? detail : 'Failed to create account');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <ScrollView
        contentContainerStyle={styles.content}
        keyboardShouldPersistTaps="handled"
      >
        <View style={[styles.header, { paddingTop: insets.top + 16 }]}>
          <Button
            mode="text"
            onPress={() => navigation.goBack()}
            textColor="#fff"
            icon={() => <Icon source="arrow-left" size={20} color="#fff" />}
            style={styles.backButton}
            contentStyle={{ flexDirection: 'row-reverse' }}
          >
            Back
          </Button>
          <Text variant="headlineSmall" style={styles.title}>
            New Account
          </Text>
        </View>

        <Surface style={styles.card} elevation={0}>
          <Text variant="labelLarge" style={styles.label}>Account Name</Text>
          <TextInput
            placeholder="e.g. Main Checking"
            value={name}
            onChangeText={setName}
            mode="outlined"
            style={styles.input}
            textContentType="none"
          />

          <Text variant="labelLarge" style={styles.label}>Currency</Text>
          <TextInput
            value={currency}
            onChangeText={setCurrency}
            mode="outlined"
            style={styles.input}
            disabled
            textContentType="none"
          />

          <Text variant="labelLarge" style={styles.label}>Initial Balance</Text>
          <TextInput
            placeholder="0.00"
            value={balance}
            onChangeText={setBalance}
            mode="outlined"
            keyboardType="decimal-pad"
            left={<TextInput.Affix text="$" />}
            style={styles.input}
            textContentType="none"
          />
        </Surface>

        <Button
          mode="contained"
          onPress={handleCreate}
          loading={isLoading}
          disabled={isLoading}
          buttonColor="#fff"
          textColor="#000"
          style={styles.createButton}
          contentStyle={styles.createButtonContent}
        >
          Create Account
        </Button>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  content: {
    paddingBottom: 40,
  },
  header: {
    paddingHorizontal: 20,
    paddingBottom: 16,
    backgroundColor: Colors.primary,
  },
  backButton: {
    alignSelf: 'flex-start',
    marginBottom: 4,
  },
  title: {
    color: '#fff',
    fontWeight: '700',
  },
  card: {
    marginHorizontal: 16,
    marginTop: 16,
    padding: 16,
    borderRadius: 12,
    backgroundColor: Colors.surfaceCard,
  },
  label: {
    color: Colors.textSecondary,
    marginBottom: 6,
    fontWeight: '600',
  },
  input: {
    marginBottom: 16,
  },
  createButton: {
    marginHorizontal: 16,
    marginTop: 24,
    borderRadius: 12,
  },
  createButtonContent: {
    height: 48,
  },
});
