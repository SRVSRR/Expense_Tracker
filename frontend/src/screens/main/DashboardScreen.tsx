import React, { useEffect, useState, useMemo } from 'react';
import { View, StyleSheet, ScrollView, RefreshControl, TouchableOpacity } from 'react-native';
import { Text, Surface } from 'react-native-paper';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Icon from '../../components/Icon';
import { useAuthStore } from '../../store/authStore';
import { useAccountStore } from '../../store/accountStore';
import { useTransactionStore } from '../../store/transactionStore';
import BalanceSummary from '../../components/BalanceSummary';
import TransactionCard from '../../components/TransactionCard';
import { forecastApi, RunwayData } from '../../api/forecast';

const TAB_BAR_HEIGHT = 56;

export default function DashboardScreen({ navigation }: any) {
  const insets = useSafeAreaInsets();
  const user = useAuthStore((state) => state.user);
  const { accounts, fetchAccounts } = useAccountStore();
  const { transactions, fetchTransactions } = useTransactionStore();
  const [runway, setRunway] = useState<RunwayData | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const loadData = async () => {
    await Promise.all([fetchAccounts(), fetchTransactions({ limit: 50 })]);
    try {
      const runwayData = await forecastApi.getRunway();
      setRunway(runwayData);
    } catch {}
  };

  useEffect(() => {
    loadData();
  }, []);

  const onRefresh = async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
  };

  const { totalIncome, totalExpenses, recentTransactions } = useMemo(() => {
    const now = new Date();
    const monthStart = new Date(now.getFullYear(), now.getMonth(), 1);
    const thisMonth = transactions.filter((t) => new Date(t.date) >= monthStart);
    return {
      totalIncome: thisMonth.filter((t) => t.type === 'income').reduce((s, t) => s + t.amount, 0),
      totalExpenses: thisMonth.filter((t) => t.type === 'expense').reduce((s, t) => s + t.amount, 0),
      recentTransactions: transactions.slice(0, 5),
    };
  }, [transactions]);

  const greeting = (() => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 17) return 'Good afternoon';
    return 'Good evening';
  })();

  return (
    <ScrollView
      style={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
    >
      <View style={[styles.header, { paddingTop: insets.top + 16 }]}>
        <Text variant="bodyMedium" style={styles.greetingLabel}>
          {greeting},
        </Text>
        <Text variant="headlineSmall" style={styles.greetingName}>
          {user?.email?.split('@')[0] || 'User'}
        </Text>
        <Text variant="bodySmall" style={styles.date}>
          {new Date().toLocaleDateString('en-US', {
            weekday: 'long',
            month: 'long',
            day: 'numeric',
          })}
        </Text>
      </View>

      <BalanceSummary accounts={accounts} />

      {/* Monthly Summary */}
      <View style={styles.summaryRow}>
        <Surface style={[styles.summaryCard, { backgroundColor: '#E8F5E9' }]} elevation={1}>
          <View style={styles.summaryIcon}>
            <Icon source="arrow-down-bold" size={18} color="#4CAF50" />
          </View>
          <Text variant="bodySmall" style={styles.summaryLabel}>
            Income
          </Text>
          <Text variant="titleMedium" style={[styles.summaryValue, { color: '#4CAF50' }]}>
            +${totalIncome.toFixed(0)}
          </Text>
        </Surface>
        <Surface style={[styles.summaryCard, { backgroundColor: '#FFEBEE' }]} elevation={1}>
          <View style={styles.summaryIcon}>
            <Icon source="arrow-up-bold" size={18} color="#F44336" />
          </View>
          <Text variant="bodySmall" style={styles.summaryLabel}>
            Expenses
          </Text>
          <Text variant="titleMedium" style={[styles.summaryValue, { color: '#F44336' }]}>
            -${totalExpenses.toFixed(0)}
          </Text>
        </Surface>
      </View>

      {/* Runway Card */}
      {runway && (
        <Surface style={styles.card} elevation={2}>
          <View style={styles.cardRow}>
            <View style={[styles.runwayIconBg, { backgroundColor: '#E3F2FD' }]}>
              <Icon source="clock-outline" size={22} color="#2196F3" />
            </View>
            <View style={styles.cardContent}>
              <Text variant="bodySmall" style={styles.secondaryText}>
                Financial Runway
              </Text>
              <Text variant="titleLarge" style={styles.runwayValue}>
                {runway.days_until_zero} days
              </Text>
              <Text variant="bodySmall" style={styles.hintText}>
                at ${runway.avg_daily_burn.toFixed(0)}/day burn rate
              </Text>
            </View>
            <Icon source="chevron-right" size={16} color="#999" />
          </View>
        </Surface>
      )}

      {/* Quick Actions */}
      <View style={styles.quickActions}>
        <TouchableOpacity
          style={styles.quickAction}
          onPress={() => navigation.navigate('Forecast')}
          activeOpacity={0.7}
        >
          <View style={[styles.quickActionIcon, { backgroundColor: '#E3F2FD' }]}>
            <Icon source="trending-up" size={20} color="#2196F3" />
          </View>
          <Text variant="bodySmall" style={styles.quickActionLabel}>
            Forecast
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={styles.quickAction}
          onPress={() => navigation.navigate('Budget')}
          activeOpacity={0.7}
        >
          <View style={[styles.quickActionIcon, { backgroundColor: '#E8F5E9' }]}>
            <Icon source="chart-pie" size={20} color="#4CAF50" />
          </View>
          <Text variant="bodySmall" style={styles.quickActionLabel}>
            Budget
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={styles.quickAction}
          onPress={() => navigation.navigate('Accounts')}
          activeOpacity={0.7}
        >
          <View style={[styles.quickActionIcon, { backgroundColor: '#FFF3E0' }]}>
            <Icon source="wallet" size={20} color="#FF9800" />
          </View>
          <Text variant="bodySmall" style={styles.quickActionLabel}>
            Accounts
          </Text>
        </TouchableOpacity>
      </View>

      {/* Recent Transactions */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Text variant="titleMedium" style={styles.sectionTitle}>
            Recent Transactions
          </Text>
          <TouchableOpacity onPress={() => navigation.navigate('Transactions')}>
            <Text variant="bodySmall" style={styles.seeAll}>
              See All
            </Text>
          </TouchableOpacity>
        </View>
        {recentTransactions.length === 0 ? (
          <Surface style={styles.emptyCard} elevation={1}>
            <Icon source="format-list-bulleted" size={32} color="#CCC" />
            <Text variant="bodyMedium" style={styles.emptyText}>
              No transactions yet
            </Text>
            <Text variant="bodySmall" style={styles.emptyHint}>
              Tap + to add your first transaction
            </Text>
          </Surface>
        ) : (
          recentTransactions.map((t) => <TransactionCard key={t.id} transaction={t} />)
        )}
      </View>

      <View style={{ height: TAB_BAR_HEIGHT + 16 }} />
    </ScrollView>
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
  greetingLabel: {
    color: 'rgba(255,255,255,0.7)',
  },
  greetingName: {
    color: '#fff',
    fontWeight: '700',
    marginTop: 2,
  },
  date: {
    color: 'rgba(255,255,255,0.6)',
    marginTop: 4,
  },
  summaryRow: {
    flexDirection: 'row',
    marginHorizontal: 16,
    marginTop: 16,
    gap: 12,
  },
  summaryCard: {
    flex: 1,
    padding: 14,
    borderRadius: 12,
    alignItems: 'center',
  },
  summaryIcon: {
    marginBottom: 6,
  },
  summaryLabel: {
    color: '#666',
  },
  summaryValue: {
    fontWeight: '700',
    marginTop: 2,
  },
  card: {
    marginHorizontal: 16,
    marginTop: 16,
    padding: 16,
    borderRadius: 12,
    backgroundColor: '#fff',
  },
  cardRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  runwayIconBg: {
    width: 44,
    height: 44,
    borderRadius: 22,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  cardContent: {
    flex: 1,
  },
  secondaryText: {
    color: '#666',
  },
  runwayValue: {
    fontWeight: '700',
    color: '#2196F3',
    marginTop: 2,
  },
  hintText: {
    color: '#999',
    marginTop: 2,
  },
  quickActions: {
    flexDirection: 'row',
    marginHorizontal: 16,
    marginTop: 16,
    gap: 12,
  },
  quickAction: {
    flex: 1,
    alignItems: 'center',
    padding: 14,
    backgroundColor: '#fff',
    borderRadius: 12,
    elevation: 1,
  },
  quickActionIcon: {
    width: 44,
    height: 44,
    borderRadius: 22,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 8,
  },
  quickActionLabel: {
    color: '#333',
    fontWeight: '600',
    textAlign: 'center',
  },
  section: {
    marginTop: 8,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    marginTop: 16,
    marginBottom: 8,
  },
  sectionTitle: {
    fontWeight: '700',
    color: '#333',
  },
  seeAll: {
    color: '#2196F3',
    fontWeight: '600',
  },
  emptyCard: {
    marginHorizontal: 16,
    padding: 32,
    borderRadius: 12,
    alignItems: 'center',
    backgroundColor: '#fff',
  },
  emptyText: {
    color: '#999',
    marginTop: 12,
    fontWeight: '600',
  },
  emptyHint: {
    color: '#CCC',
    marginTop: 4,
  },
});
