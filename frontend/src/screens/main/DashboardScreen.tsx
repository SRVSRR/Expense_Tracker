import React, { useEffect, useState, useMemo } from 'react';
import { View, StyleSheet, ScrollView, RefreshControl, TouchableOpacity } from 'react-native';
import { Text, Surface, FAB } from 'react-native-paper';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Icon from '../../components/Icon';
import { Colors } from '../../theme/colors';
import { useAuthStore } from '../../store/authStore';
import { useAccountStore } from '../../store/accountStore';
import { useTransactionStore } from '../../store/transactionStore';
import BalanceSummary from '../../components/BalanceSummary';
import TransactionCard from '../../components/TransactionCard';
import { forecastApi, RunwayData } from '../../api/forecast';

const TAB_BAR_HEIGHT = 52;

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
    <>
      <ScrollView
        style={styles.container}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={Colors.primary} />}
      >
        <View style={[styles.header, { paddingTop: insets.top + 16 }]}>
          <Text variant="bodySmall" style={styles.greetingLabel}>
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
          <Surface style={[styles.summaryCard, { backgroundColor: Colors.incomeSurface }]} elevation={0}>
            <View style={styles.summaryIcon}>
              <Icon source="arrow-down-bold" size={16} color={Colors.income} />
            </View>
            <Text variant="bodySmall" style={styles.summaryLabel}>
              Income
            </Text>
            <Text variant="titleMedium" style={[styles.summaryValue, { color: Colors.income }]}>
              +${totalIncome.toFixed(0)}
            </Text>
          </Surface>
          <Surface style={[styles.summaryCard, { backgroundColor: Colors.expenseSurface }]} elevation={0}>
            <View style={styles.summaryIcon}>
              <Icon source="arrow-up-bold" size={16} color={Colors.expense} />
            </View>
            <Text variant="bodySmall" style={styles.summaryLabel}>
              Expenses
            </Text>
            <Text variant="titleMedium" style={[styles.summaryValue, { color: Colors.expense }]}>
              -${totalExpenses.toFixed(0)}
            </Text>
          </Surface>
        </View>

        {/* Runway Card */}
        {runway && (
          <Surface style={styles.card} elevation={0}>
            <View style={styles.cardRow}>
              <View style={[styles.runwayIconBg, { backgroundColor: Colors.primarySurface }]}>
                <Icon source="clock-outline" size={20} color={Colors.primary} />
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
              <Icon source="chevron-right" size={14} color={Colors.textTertiary} />
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
            <View style={[styles.quickActionIcon, { backgroundColor: Colors.primarySurface }]}>
              <Icon source="trending-up" size={18} color={Colors.primary} />
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
            <View style={[styles.quickActionIcon, { backgroundColor: Colors.tertiarySurface }]}>
              <Icon source="chart-pie" size={18} color={Colors.tertiary} />
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
            <View style={[styles.quickActionIcon, { backgroundColor: Colors.warningSurface }]}>
              <Icon source="wallet" size={18} color={Colors.warning} />
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
            <Surface style={styles.emptyCard} elevation={0}>
              <Icon source="format-list-bulleted" size={32} color={Colors.textDisabled} />
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

        <View style={{ height: TAB_BAR_HEIGHT + 24 }} />
      </ScrollView>

      <FAB
        icon="plus-circle"
        style={[styles.fab, { bottom: insets.bottom + TAB_BAR_HEIGHT + 16 }]}
        onPress={() => navigation.navigate('AddTransaction')}
        color="#fff"
      />
    </>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  header: {
    paddingHorizontal: 20,
    paddingBottom: 16,
    backgroundColor: Colors.primary,
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
    color: Colors.textSecondary,
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
    backgroundColor: Colors.surfaceCard,
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
    color: Colors.textSecondary,
  },
  runwayValue: {
    fontWeight: '700',
    color: Colors.primary,
    marginTop: 2,
  },
  hintText: {
    color: Colors.textTertiary,
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
    backgroundColor: Colors.surfaceCard,
    borderRadius: 12,
  },
  quickActionIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 8,
  },
  quickActionLabel: {
    color: Colors.textPrimary,
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
    color: Colors.textPrimary,
  },
  seeAll: {
    color: Colors.primary,
    fontWeight: '600',
  },
  emptyCard: {
    marginHorizontal: 16,
    padding: 32,
    borderRadius: 12,
    alignItems: 'center',
    backgroundColor: Colors.surfaceCard,
  },
  emptyText: {
    color: Colors.textSecondary,
    marginTop: 12,
    fontWeight: '600',
  },
  emptyHint: {
    color: Colors.textTertiary,
    marginTop: 4,
  },
  fab: {
    position: 'absolute',
    right: 20,
    backgroundColor: Colors.primary,
    borderRadius: 16,
    elevation: 4,
  },
});
