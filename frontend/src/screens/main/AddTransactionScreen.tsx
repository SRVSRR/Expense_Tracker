import React, { useState, useEffect } from 'react';
import { View, StyleSheet, ScrollView, Alert } from 'react-native';
import {
  TextInput,
  Button,
  Text,
  SegmentedButtons,
  Surface,
  Menu,
  TouchableRipple,
  Checkbox,
} from 'react-native-paper';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Icon from '../../components/Icon';
import { useTransactionStore } from '../../store/transactionStore';
import { useAccountStore } from '../../store/accountStore';
import { useCategoryStore } from '../../store/categoryStore';

export default function AddTransactionScreen({ navigation }: any) {
  const insets = useSafeAreaInsets();
  const [type, setType] = useState<'income' | 'expense'>('expense');
  const [amount, setAmount] = useState('');
  const [description, setDescription] = useState('');
  const [merchant, setMerchant] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [selectedAccountId, setSelectedAccountId] = useState('');
  const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
  const [isRecurring, setIsRecurring] = useState(false);
  const [categoryMenuVisible, setCategoryMenuVisible] = useState(false);
  const [accountMenuVisible, setAccountMenuVisible] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const { createTransaction } = useTransactionStore();
  const { accounts, fetchAccounts } = useAccountStore();
  const { categories, fetchCategories, getCategoriesByType } = useCategoryStore();

  useEffect(() => {
    fetchAccounts();
    fetchCategories();
  }, []);

  const filteredCategories = getCategoriesByType(type);
  const selectedAccount = accounts.find((a) => a.id === selectedAccountId);

  const handleSubmit = async () => {
    if (!amount || !description || !selectedCategory || !selectedAccountId) {
      Alert.alert('Error', 'Please fill in all required fields');
      return;
    }

    setIsLoading(true);
    try {
      await createTransaction({
        account_id: selectedAccountId,
        type,
        amount: parseFloat(amount),
        category: selectedCategory,
        description,
        merchant: merchant || undefined,
        date,
        is_recurring: isRecurring,
      });
      Alert.alert('Success', 'Transaction added!', [
        { text: 'OK', onPress: () => navigation.goBack() },
      ]);
    } catch (error: any) {
      Alert.alert('Error', error.response?.data?.detail || 'Failed to add transaction');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <View style={[styles.header, { paddingTop: insets.top + 16 }]}>
        <Text variant="headlineSmall" style={styles.title}>
          Add Transaction
        </Text>
      </View>

      <Surface style={styles.card} elevation={2}>
        <Text variant="titleMedium" style={styles.label}>
          Type
        </Text>
        <SegmentedButtons
          value={type}
          onValueChange={(v) => {
            setType(v as 'income' | 'expense');
            setSelectedCategory('');
          }}
          buttons={[
            { value: 'income', label: 'Income' },
            { value: 'expense', label: 'Expense' },
          ]}
          style={styles.segment}
        />

        <TextInput
          label="Amount *"
          value={amount}
          onChangeText={setAmount}
          mode="outlined"
          keyboardType="decimal-pad"
          left={<TextInput.Affix text="$" />}
          style={styles.input}
        />

        <TextInput
          label="Description *"
          value={description}
          onChangeText={setDescription}
          mode="outlined"
          style={styles.input}
        />

        <TextInput
          label="Merchant (optional)"
          value={merchant}
          onChangeText={setMerchant}
          mode="outlined"
          style={styles.input}
        />

        <TextInput
          label="Date *"
          value={date}
          onChangeText={setDate}
          mode="outlined"
          placeholder="YYYY-MM-DD"
          style={styles.input}
        />

        <Text variant="titleMedium" style={styles.label}>
          Account *
        </Text>
        <Menu
          visible={accountMenuVisible}
          onDismiss={() => setAccountMenuVisible(false)}
          anchor={
            <TouchableRipple
              onPress={() => setAccountMenuVisible(true)}
              style={styles.selector}
            >
              <View style={styles.selectorContent}>
                <Text variant="bodyLarge">
                  {selectedAccount ? selectedAccount.name : 'Select account'}
                </Text>
                <Icon source="chevron-down" size={20} color="#666" />
              </View>
            </TouchableRipple>
          }
        >
          {accounts.map((account) => (
            <Menu.Item
              key={account.id}
              onPress={() => {
                setSelectedAccountId(account.id);
                setAccountMenuVisible(false);
              }}
              title={account.name}
            />
          ))}
        </Menu>

        <Text variant="titleMedium" style={styles.label}>
          Category *
        </Text>
        <Menu
          visible={categoryMenuVisible}
          onDismiss={() => setCategoryMenuVisible(false)}
          anchor={
            <TouchableRipple
              onPress={() => setCategoryMenuVisible(true)}
              style={styles.selector}
            >
              <View style={styles.selectorContent}>
                <Text variant="bodyLarge">
                  {selectedCategory || 'Select category'}
                </Text>
                <Icon source="chevron-down" size={20} color="#666" />
              </View>
            </TouchableRipple>
          }
        >
          {filteredCategories.map((cat) => (
            <Menu.Item
              key={cat.id}
              onPress={() => {
                setSelectedCategory(cat.name);
                setCategoryMenuVisible(false);
              }}
              title={cat.name}
            />
          ))}
        </Menu>

        <TouchableRipple
          onPress={() => setIsRecurring(!isRecurring)}
          style={styles.recurringToggle}
        >
          <View style={styles.recurringRow}>
            <Checkbox
              status={isRecurring ? 'checked' : 'unchecked'}
              onPress={() => setIsRecurring(!isRecurring)}
            />
            <Text variant="bodyLarge" style={styles.recurringText}>
              Recurring transaction
            </Text>
          </View>
        </TouchableRipple>

        <Button
          mode="contained"
          onPress={handleSubmit}
          loading={isLoading}
          disabled={isLoading}
          style={styles.button}
          buttonColor="#2196F3"
        >
          Add Transaction
        </Button>
      </Surface>

      <View style={{ height: 80 }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F5',
  },
  content: {
    paddingBottom: 30,
  },
  header: {
    padding: 16,
    backgroundColor: '#2196F3',
  },
  title: {
    color: '#fff',
    fontWeight: '700',
  },
  card: {
    marginHorizontal: 16,
    marginTop: 16,
    padding: 20,
    borderRadius: 16,
    backgroundColor: '#fff',
  },
  label: {
    fontWeight: '600',
    marginBottom: 8,
  },
  segment: {
    marginBottom: 16,
  },
  input: {
    marginBottom: 16,
  },
  selector: {
    borderWidth: 1,
    borderColor: '#79747E',
    borderRadius: 4,
    padding: 16,
    marginBottom: 16,
  },
  selectorContent: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  recurringToggle: {
    marginBottom: 20,
  },
  recurringRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  recurringText: {
    flex: 1,
  },
  button: {
    borderRadius: 8,
    paddingVertical: 4,
  },
});
