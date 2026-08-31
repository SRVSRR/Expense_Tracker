import React, { useEffect, useState } from 'react';
import { View, StyleSheet, FlatList, RefreshControl } from 'react-native';
import { Text, SegmentedButtons, Surface } from 'react-native-paper';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Icon from '../../components/Icon';
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

  const net = totalIncome - totalExpenses;

  return (
    <View style={styles.container}>
      <View style={[styles.header, { paddingTop: insets.top + 16 }]}>
        <Text variant="headlineSmall" style={styles.title}>
          Transactions
        </Text>
        <Text variant="bodySmall" style={styles.subtitle}>
          {transactions.length} transaction{transactions.length !== 1 ? 's' : ''} this period
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
          <View style={[styles.summaryDot, { backgroundColor: '#4CAF50' }]} />
          <Text variant="bodySmall" style={styles.summaryLabel}>
            Income
          </Text>
          <Text variant="titleMedium" style={styles.incomeValue}>
            +${totalIncome.toFixed(2)}
          </Text>
        </View>
        <View style={styles.divider} />
        <View style={styles.summaryItem}>
          <View style={[styles.summaryDot, { backgroundColor: '#F44336' }]} />
          <Text variant="bodySmall" style={styles.summaryLabel}>
            Expenses
          </Text>
          <Text variant="titleMedium" style={styles.expenseValue}>
            -${totalExpenses.toFixed(2)}
          </Text>
        </View>
        <View style={styles.divider} />
        <View style={styles.summaryItem}>
          <Text variant="bodySmall" style={styles.summaryLabel}>
            Net
          </Text>
          <Text
            variant="titleMedium"
            style={net >= 0 ? styles.incomeValue : styles.expenseValue}
          >
            {net >= 0 ? '+' : ''}${net.toFixed(2)}
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
          <View style={styles.emptyContainer}>
            <View style={styles.emptyIconBg}>
              <Icon source="format-list-bulleted" size={40} color="#CCC" />
            </View>
            <Text variant="bodyLarge" style={styles.emptyTitle}>
              No transactions yet
            </Text>
            <Text variant="bodySmall" style={styles.emptyHint}>
              Your transactions will appear here{'\n'}once you add them
            </Text>
          </View>
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
    paddingHorizontal: 20,
    paddingBottom: 16,
    backgroundColor: '#2196F3',
  },
  title: {
    color: '#fff',
    fontWeight: '700',
  },
  subtitle: {
    color: 'rgba(255,255,255,0.7)',
    marginTop: 4,
  },
  filter: {
    marginHorizontal: 16,
    marginTop: 16,
  },
  summary: {
    flexDirection: 'row',
    marginHorizontal: 16,
    marginTop: 12,
    padding: 14,
    borderRadius: 12,
    backgroundColor: '#fff',
    alignItems: 'center',
  },
  summaryItem: {
    flex: 1,
    alignItems: 'center',
  },
  summaryDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    marginBottom: 4,
  },
  summaryLabel: {
    color: '#666',
  },
  incomeValue: {
    fontWeight: '700',
    color: '#4CAF50',
    marginTop: 2,
  },
  expenseValue: {
    fontWeight: '700',
    color: '#F44336',
    marginTop: 2,
  },
  divider: {
    width: 1,
    height: 32,
    backgroundColor: '#E8E8E8',
  },
  list: {
    paddingTop: 4,
  },
  emptyContainer: {
    alignItems: 'center',
    paddingTop: 48,
    paddingHorizontal: 32,
  },
  emptyIconBg: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: '#F0F0F0',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
  },
  emptyTitle: {
    color: '#666',
    fontWeight: '600',
    marginBottom: 8,
  },
  emptyHint: {
    color: '#999',
    textAlign: 'center',
    lineHeight: 20,
  },
});
