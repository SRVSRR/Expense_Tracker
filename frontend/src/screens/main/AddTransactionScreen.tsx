import React, { useState, useEffect } from 'react';
import { View, StyleSheet, ScrollView, Alert, TouchableOpacity } from 'react-native';
import {
  TextInput,
  Button,
  Text,
  SegmentedButtons,
  Surface,
  Menu,
  Checkbox,
  Divider,
  TouchableRipple,
} from 'react-native-paper';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Icon from '../../components/Icon';
import { Colors } from '../../theme/colors';
import { useTransactionStore } from '../../store/transactionStore';
import { useAccountStore } from '../../store/accountStore';
import { useCategoryStore } from '../../store/categoryStore';

const TAB_BAR_HEIGHT = 52;

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
      Alert.alert('Missing Fields', 'Please fill in all required fields.');
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

      {/* Type Toggle */}
      <Surface style={styles.card} elevation={0}>
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
        />
      </Surface>

      {/* Amount Card */}
      <Surface style={styles.card} elevation={0}>
        <View style={styles.amountSection}>
          <Text variant="bodySmall" style={styles.fieldLabel}>
            Amount
          </Text>
          <View style={styles.amountInput}>
            <Text variant="headlineMedium" style={styles.dollarSign}>
              $
            </Text>
            <TextInput
              value={amount}
              onChangeText={setAmount}
              mode="flat"
              keyboardType="decimal-pad"
              placeholder="0.00"
              placeholderTextColor={Colors.textDisabled}
              style={styles.amountField}
              underlineColor="transparent"
              activeUnderlineColor="transparent"
            />
          </View>
          <Divider style={styles.divider} />
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
        </View>
      </Surface>

      {/* Account & Category */}
      <Surface style={styles.card} elevation={0}>
        <Text variant="bodySmall" style={styles.sectionLabel}>
          ACCOUNT & CATEGORY
        </Text>

        <Text variant="bodyMedium" style={styles.fieldLabel}>
          Account *
        </Text>
        <Menu
          visible={accountMenuVisible}
          onDismiss={() => setAccountMenuVisible(false)}
          anchor={
            <TouchableOpacity
              onPress={() => setAccountMenuVisible(true)}
              style={styles.selector}
              activeOpacity={0.7}
            >
              <View style={styles.selectorContent}>
                <View style={styles.selectorLeft}>
                  <Icon source="wallet" size={18} color={Colors.primary} />
                  <Text
                    variant="bodyMedium"
                    style={selectedAccount ? styles.selectorText : styles.selectorPlaceholder}
                  >
                    {selectedAccount ? selectedAccount.name : 'Select account'}
                  </Text>
                </View>
                <Icon source="chevron-down" size={14} color={Colors.textTertiary} />
              </View>
            </TouchableOpacity>
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

        <Text variant="bodyMedium" style={[styles.fieldLabel, { marginTop: 12 }]}>
          Category *
        </Text>
        <Menu
          visible={categoryMenuVisible}
          onDismiss={() => setCategoryMenuVisible(false)}
          anchor={
            <TouchableOpacity
              onPress={() => setCategoryMenuVisible(true)}
              style={styles.selector}
              activeOpacity={0.7}
            >
              <View style={styles.selectorContent}>
                <View style={styles.selectorLeft}>
                  <Icon source="tag" size={18} color={Colors.primary} />
                  <Text
                    variant="bodyMedium"
                    style={selectedCategory ? styles.selectorText : styles.selectorPlaceholder}
                  >
                    {selectedCategory || 'Select category'}
                  </Text>
                </View>
                <Icon source="chevron-down" size={14} color={Colors.textTertiary} />
              </View>
            </TouchableOpacity>
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
      </Surface>

      {/* Options */}
      <Surface style={styles.card} elevation={0}>
        <TouchableRipple
          onPress={() => setIsRecurring(!isRecurring)}
          style={styles.recurringToggle}
        >
          <View style={styles.recurringRow}>
            <View style={styles.recurringLeft}>
              <Icon source="repeat" size={20} color={Colors.textSecondary} />
              <View style={{ marginLeft: 12 }}>
                <Text variant="bodyMedium" style={styles.recurringTitle}>
                  Recurring Transaction
                </Text>
                <Text variant="bodySmall" style={styles.recurringHint}>
                  Mark if this repeats regularly
                </Text>
              </View>
            </View>
            <Checkbox
              status={isRecurring ? 'checked' : 'unchecked'}
              onPress={() => setIsRecurring(!isRecurring)}
              color={Colors.primary}
            />
          </View>
        </TouchableRipple>
      </Surface>

      {/* Submit */}
      <View style={styles.submitSection}>
        <Button
          mode="contained"
          onPress={handleSubmit}
          loading={isLoading}
          disabled={isLoading}
          style={styles.submitButton}
          buttonColor="#fff"
          contentStyle={{ paddingVertical: 6 }}
        >
          Add Transaction
        </Button>
      </View>

      <View style={{ height: TAB_BAR_HEIGHT + 16 }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  content: {
    paddingBottom: 30,
  },
  header: {
    paddingHorizontal: 20,
    paddingBottom: 16,
    backgroundColor: Colors.primary,
  },
  title: {
    color: '#fff',
    fontWeight: '700',
  },
  card: {
    marginHorizontal: 16,
    marginTop: 12,
    padding: 16,
    borderRadius: 12,
    backgroundColor: Colors.surfaceCard,
  },
  sectionLabel: {
    color: Colors.textTertiary,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 12,
  },
  fieldLabel: {
    color: Colors.textSecondary,
    fontWeight: '600',
    marginBottom: 6,
  },
  amountSection: {},
  amountInput: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  dollarSign: {
    color: Colors.textPrimary,
    fontWeight: '700',
    marginRight: 4,
  },
  amountField: {
    flex: 1,
    backgroundColor: 'transparent',
    fontSize: 32,
    fontWeight: '700',
    color: Colors.textPrimary,
  },
  divider: {
    marginBottom: 12,
    backgroundColor: Colors.divider,
  },
  input: {
    marginBottom: 12,
    backgroundColor: Colors.surfaceElevated,
  },
  selector: {
    borderWidth: 1,
    borderColor: Colors.border,
    borderRadius: 8,
    padding: 14,
    backgroundColor: Colors.surfaceElevated,
  },
  selectorContent: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  selectorLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  selectorText: {
    color: Colors.textPrimary,
  },
  selectorPlaceholder: {
    color: Colors.textTertiary,
  },
  recurringToggle: {
    paddingVertical: 4,
  },
  recurringRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  recurringLeft: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  recurringTitle: {
    fontWeight: '600',
    color: Colors.textPrimary,
  },
  recurringHint: {
    color: Colors.textTertiary,
    marginTop: 2,
  },
  submitSection: {
    marginHorizontal: 16,
    marginTop: 20,
  },
  submitButton: {
    borderRadius: 10,
  },
});
