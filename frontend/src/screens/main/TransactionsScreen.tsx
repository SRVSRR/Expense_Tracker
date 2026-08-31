import React, { useEffect, useState } from 'react';
import { View, StyleSheet, FlatList, RefreshControl } from 'react-native';
import { Text, SegmentedButtons, Surface } from 'react-native-paper';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useTransactionStore } from '../../store/transactionStore';
import TransactionCard from '../../components/TransactionCard';

const TAB_BAR_HEIGHT = 56;

export default function TransactionsScreen() {
  const insets = useSafeAreaInsets();
  const { transactions, isLoading, fetchTransactions, filters, setFilters } = useTransactionStore();
  const [typeFilter, setTypeFilter] = useState('all');
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    const newFilters = { ...filters };
    if (typeFilter !== 'all') {
      newFilters.type = typeFilter;
    } else {
      delete newFilters.type;
    }
    setFilters(newFilters);
    fetchTransactions(newFilters);
  }, [typeFilter]);

  const onRefresh = async () => {
    setRefreshing(true);
    await fetchTransactions();
    setRefreshing(false);
  };

  const totalIncome = transactions
    .filter((t) => t.type === 'income')
    .reduce((sum, t) => sum + t.amount, 0);

  const totalExpenses = transactions
    .filter((t) => t.type === 'expense')
    .reduce((sum, t) => sum + t.amount, 0);

  return (
    <View style={styles.container}>
      <View style={[styles.header, { paddingTop: insets.top + 16 }]}>
        <Text variant="headlineSmall" style={styles.title}>
          Transactions
        </Text>
      </View>

      <SegmentedButtons
        value={typeFilter}
        onValueChange={setTypeFilter}
        buttons={[
          { value: 'all', label: 'All' },
          { value: 'income', label: 'Income' },
          { value: 'expense', label: 'Expense' },
        ]}
        style={styles.filter}
      />

      <Surface style={styles.summary} elevation={1}>
        <View style={styles.summaryItem}>
          <Text variant="bodySmall" style={styles.summaryLabel}>
            Income
          </Text>
          <Text variant="titleMedium" style={[styles.summaryValue, { color: '#4CAF50' }]}>
            +${totalIncome.toFixed(2)}
          </Text>
        </View>
        <View style={styles.divider} />
        <View style={styles.summaryItem}>
          <Text variant="bodySmall" style={styles.summaryLabel}>
            Expenses
          </Text>
          <Text variant="titleMedium" style={[styles.summaryValue, { color: '#F44336' }]}>
            -${totalExpenses.toFixed(2)}
          </Text>
        </View>
      </Surface>

      <FlatList
        data={transactions}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => <TransactionCard transaction={item} />}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
        contentContainerStyle={[styles.list, { paddingBottom: TAB_BAR_HEIGHT + 16 }]}
        ListEmptyComponent={
          <Text variant="bodyMedium" style={styles.empty}>
            No transactions found
          </Text>
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F5',
  },
  header: {
    padding: 16,
    backgroundColor: '#2196F3',
  },
  title: {
    color: '#fff',
    fontWeight: '700',
  },
  filter: {
    marginHorizontal: 16,
    marginTop: 16,
  },
  summary: {
    flexDirection: 'row',
    marginHorizontal: 16,
    marginTop: 12,
    padding: 16,
    borderRadius: 12,
    backgroundColor: '#fff',
  },
  summaryItem: {
    flex: 1,
    alignItems: 'center',
  },
  summaryLabel: {
    color: '#666',
  },
  summaryValue: {
    fontWeight: '700',
    marginTop: 4,
  },
  divider: {
    width: 1,
    backgroundColor: '#E0E0E0',
    marginVertical: 4,
  },
  list: {
    paddingTop: 4,
  },
  empty: {
    textAlign: 'center',
    color: '#666',
    marginTop: 40,
  },
});
