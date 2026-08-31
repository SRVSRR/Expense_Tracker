import React, { useState, useEffect, useCallback, useRef } from 'react';
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
import { useRecurringStore } from '../../store/recurringStore';
import { categorizeApi, SuggestResponse } from '../../api/categorize';

const TAB_BAR_HEIGHT = 52;

const FREQUENCIES = [
  { value: 'weekly', label: 'Weekly' },
  { value: 'biweekly', label: 'Bi-weekly' },
  { value: 'monthly', label: 'Monthly' },
  { value: 'quarterly', label: 'Quarterly' },
  { value: 'yearly', label: 'Yearly' },
];

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
  const [frequency, setFrequency] = useState('monthly');
  const [nextDate, setNextDate] = useState('');
  const [categoryMenuVisible, setCategoryMenuVisible] = useState(false);
  const [accountMenuVisible, setAccountMenuVisible] = useState(false);
  const [frequencyMenuVisible, setFrequencyMenuVisible] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  // Auto-suggest state
  const [suggestion, setSuggestion] = useState<SuggestResponse | null>(null);
  const [suggestionAccepted, setSuggestionAccepted] = useState(false);
  const suggestTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);

  const { createTransaction } = useTransactionStore();
  const { accounts, fetchAccounts } = useAccountStore();
  const { categories, fetchCategories, getCategoriesByType } = useCategoryStore();
  const { createRule } = useRecurringStore();

  useEffect(() => {
    fetchAccounts();
    fetchCategories();
    const d = new Date();
    d.setMonth(d.getMonth() + 1);
    setNextDate(d.toISOString().split('T')[0]);
  }, []);

  // Debounced auto-suggest
  const fetchSuggestion = useCallback(async (desc: string, mer: string) => {
    if (desc.length < 3) {
      setSuggestion(null);
      return;
    }
    try {
      const result = await categorizeApi.suggest(desc, mer || undefined);
      setSuggestion(result);
      setSuggestionAccepted(false);
    } catch {}
  }, []);

  const handleDescriptionChange = (text: string) => {
    setDescription(text);
    if (suggestTimeout.current) clearTimeout(suggestTimeout.current);
    suggestTimeout.current = setTimeout(() => {
      fetchSuggestion(text, merchant);
    }, 400);
  };

  const handleMerchantChange = (text: string) => {
    setMerchant(text);
    if (suggestTimeout.current) clearTimeout(suggestTimeout.current);
    suggestTimeout.current = setTimeout(() => {
      fetchSuggestion(description, text);
    }, 400);
  };

  const acceptSuggestion = () => {
    if (suggestion?.suggested_category) {
      setSelectedCategory(suggestion.suggested_category);
      setSuggestionAccepted(true);
    }
  };

  const dismissSuggestion = () => {
    setSuggestion(null);
    setSuggestionAccepted(true);
  };

  const filteredCategories = getCategoriesByType(type);
  const selectedAccount = accounts.find((a) => a.id === selectedAccountId);
  const selectedFreqLabel = FREQUENCIES.find((f) => f.value === frequency)?.label || 'Monthly';

  const handleSubmit = async () => {
    if (!amount || !description || !selectedCategory || !selectedAccountId) {
      Alert.alert('Missing Fields', 'Please fill in all required fields.');
      return;
    }

    // Log correction if user overrode the suggestion
    if (suggestion?.suggested_category && suggestion.suggested_category !== selectedCategory) {
      categorizeApi.logCorrection({
        description,
        merchant: merchant || undefined,
        suggested_category: suggestion.suggested_category,
        corrected_category: selectedCategory,
      }).catch(() => {});
    }

    setIsLoading(true);
    try {
      const transaction = await createTransaction({
        account_id: selectedAccountId,
        type,
        amount: parseFloat(amount),
        category: selectedCategory,
        description,
        merchant: merchant || undefined,
        date,
        is_recurring: isRecurring ? 1 : 0,
      });

      if (isRecurring && nextDate) {
        const patternMap: Record<string, string> = {
          weekly: 'weekly', biweekly: 'weekly', monthly: 'monthly',
          quarterly: 'monthly', yearly: 'yearly',
        };
        const freqMap: Record<string, number> = {
          weekly: 1, biweekly: 2, monthly: 1, quarterly: 3, yearly: 1,
        };

        await createRule({
          transaction_id: transaction.id,
          pattern: patternMap[frequency] || 'monthly',
          frequency: freqMap[frequency] || 1,
          expected_amount: parseFloat(amount),
          expected_date: new Date(nextDate).toISOString(),
        });
      }

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
            onChangeText={handleDescriptionChange}
            mode="outlined"
            style={styles.input}
          />
          <TextInput
            label="Merchant (optional)"
            value={merchant}
            onChangeText={handleMerchantChange}
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

      {/* Auto-suggest chip */}
      {suggestion?.suggested_category && !suggestionAccepted && (
        <Surface style={styles.suggestCard} elevation={0}>
          <View style={styles.suggestRow}>
            <View style={styles.suggestLeft}>
              <Icon source="tag" size={16} color={Colors.tertiary} />
              <Text variant="bodySmall" style={styles.suggestLabel}>
                Suggested:
              </Text>
              <Text variant="bodyMedium" style={styles.suggestCategory}>
                {suggestion.suggested_category}
              </Text>
              <View style={[styles.confBadge, { backgroundColor: suggestion.confidence === 'high' ? Colors.incomeSurface : Colors.warningSurface }]}>
                <Text variant="bodySmall" style={[styles.confText, { color: suggestion.confidence === 'high' ? Colors.income : Colors.warning }]}>
                  {suggestion.confidence}
                </Text>
              </View>
            </View>
            <View style={styles.suggestActions}>
              <TouchableOpacity onPress={acceptSuggestion} style={styles.suggestBtn}>
                <Icon source="check" size={16} color={Colors.income} />
              </TouchableOpacity>
              <TouchableOpacity onPress={dismissSuggestion} style={styles.suggestBtn}>
                <Icon source="close" size={16} color={Colors.expense} />
              </TouchableOpacity>
            </View>
          </View>
        </Surface>
      )}

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

      {/* Recurring */}
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
              color={Colors.tertiary}
            />
          </View>
        </TouchableRipple>

        {isRecurring && (
          <>
            <Divider style={[styles.divider, { marginTop: 8 }]} />
            <Text variant="bodySmall" style={styles.sectionLabel}>
              RECURRENCE SETTINGS
            </Text>

            <Text variant="bodyMedium" style={styles.fieldLabel}>
              Frequency
            </Text>
            <Menu
              visible={frequencyMenuVisible}
              onDismiss={() => setFrequencyMenuVisible(false)}
              anchor={
                <TouchableOpacity
                  onPress={() => setFrequencyMenuVisible(true)}
                  style={styles.selector}
                  activeOpacity={0.7}
                >
                  <View style={styles.selectorContent}>
                    <View style={styles.selectorLeft}>
                      <Icon source="repeat" size={18} color={Colors.tertiary} />
                      <Text variant="bodyMedium" style={styles.selectorText}>
                        {selectedFreqLabel}
                      </Text>
                    </View>
                    <Icon source="chevron-down" size={14} color={Colors.textTertiary} />
                  </View>
                </TouchableOpacity>
              }
            >
              {FREQUENCIES.map((freq) => (
                <Menu.Item
                  key={freq.value}
                  onPress={() => {
                    setFrequency(freq.value);
                    setFrequencyMenuVisible(false);
                  }}
                  title={freq.label}
                />
              ))}
            </Menu>

            <TextInput
              label="Next Date"
              value={nextDate}
              onChangeText={setNextDate}
              mode="outlined"
              placeholder="YYYY-MM-DD"
              style={[styles.input, { marginTop: 12 }]}
            />
          </>
        )}
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
          textColor="#000"
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
  container: { flex: 1, backgroundColor: Colors.background },
  content: { paddingBottom: 30 },
  header: { paddingHorizontal: 20, paddingBottom: 16, backgroundColor: Colors.primary },
  title: { color: '#fff', fontWeight: '700' },
  card: {
    marginHorizontal: 16, marginTop: 12, padding: 16,
    borderRadius: 12, backgroundColor: Colors.surfaceCard,
  },
  sectionLabel: { color: Colors.textTertiary, fontWeight: '600', letterSpacing: 0.5, marginBottom: 12 },
  fieldLabel: { color: Colors.textSecondary, fontWeight: '600', marginBottom: 6 },
  amountSection: {},
  amountInput: { flexDirection: 'row', alignItems: 'center', marginBottom: 8 },
  dollarSign: { color: Colors.textPrimary, fontWeight: '700', marginRight: 4 },
  amountField: { flex: 1, backgroundColor: 'transparent', fontSize: 32, fontWeight: '700', color: Colors.textPrimary },
  divider: { marginBottom: 12, backgroundColor: Colors.divider },
  input: { marginBottom: 12, backgroundColor: Colors.surfaceElevated },
  selector: { borderWidth: 1, borderColor: Colors.border, borderRadius: 8, padding: 14, backgroundColor: Colors.surfaceElevated },
  selectorContent: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  selectorLeft: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  selectorText: { color: Colors.textPrimary },
  selectorPlaceholder: { color: Colors.textTertiary },
  suggestCard: {
    marginHorizontal: 16, marginTop: 10, padding: 12,
    borderRadius: 10, backgroundColor: Colors.tertiarySurface,
    borderWidth: 1, borderColor: Colors.tertiary,
  },
  suggestRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  suggestLeft: { flexDirection: 'row', alignItems: 'center', gap: 6, flex: 1 },
  suggestLabel: { color: Colors.textSecondary },
  suggestCategory: { fontWeight: '700', color: Colors.tertiary },
  confBadge: { paddingHorizontal: 6, paddingVertical: 2, borderRadius: 4, marginLeft: 4 },
  confText: { fontWeight: '600', fontSize: 10 },
  suggestActions: { flexDirection: 'row', gap: 8 },
  suggestBtn: { padding: 6 },
  recurringToggle: { paddingVertical: 4 },
  recurringRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  recurringLeft: { flexDirection: 'row', alignItems: 'center' },
  recurringTitle: { fontWeight: '600', color: Colors.textPrimary },
  recurringHint: { color: Colors.textTertiary, marginTop: 2 },
  submitSection: { marginHorizontal: 16, marginTop: 20 },
  submitButton: { borderRadius: 10 },
});
