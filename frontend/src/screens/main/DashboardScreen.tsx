import React, { useEffect, useState } from 'react';
import { View, StyleSheet, ScrollView, RefreshControl } from 'react-native';
import { Text, Card, Button, Surface } from 'react-native-paper';
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
    await Promise.all([fetchAccounts(), fetchTransactions({ limit: 5 })]);
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

  return (
    <ScrollView
      style={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
    >
      <View style={[styles.header, { paddingTop: insets.top + 16 }]}>
        <Text variant="headlineSmall" style={styles.greeting}>
          Hello, {user?.email?.split('@')[0] || 'User'}
        </Text>
        <Text variant="bodyMedium" style={styles.date}>
          {new Date().toLocaleDateString('en-US', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric',
          })}
        </Text>
      </View>

      <BalanceSummary accounts={accounts} />

      {runway && (
        <Surface style={styles.card} elevation={2}>
          <View style={styles.cardRow}>
            <Icon source="clock-outline" size={24} color="#2196F3" />
            <View style={styles.cardContent}>
              <Text variant="bodyMedium" style={styles.secondaryText}>
                Runway
              </Text>
              <Text variant="titleLarge" style={styles.primaryValue}>
                {runway.days_until_zero} days
              </Text>
              <Text variant="bodySmall" style={styles.hintText}>
                Until balance reaches $0 at current burn rate
              </Text>
            </View>
          </View>
        </Surface>
      )}

      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Text variant="titleMedium" style={styles.sectionTitle}>
            Recent Transactions
          </Text>
          <Button
            mode="text"
            compact
            onPress={() => navigation.navigate('Transactions')}
            textColor="#2196F3"
          >
            See All
          </Button>
        </View>
        {transactions.length === 0 ? (
          <Card style={styles.card}>
            <Card.Content>
              <Text variant="bodyMedium" style={styles.emptyText}>
                No transactions yet. Add your first one!
              </Text>
            </Card.Content>
          </Card>
        ) : (
          transactions.map((t) => <TransactionCard key={t.id} transaction={t} />)
        )}
      </View>

      <View style={styles.quickLinks}>
        <Button
          mode="contained"
          onPress={() => navigation.navigate('Forecast')}
          style={styles.quickButton}
          buttonColor="#2196F3"
        >
          View Forecast
        </Button>
        <Button
          mode="contained"
          onPress={() => navigation.navigate('Budget')}
          style={styles.quickButton}
          buttonColor="#4CAF50"
        >
          Budget Analysis
        </Button>
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
    padding: 16,
    backgroundColor: '#2196F3',
  },
  greeting: {
    color: '#fff',
    fontWeight: '700',
  },
  date: {
    color: 'rgba(255,255,255,0.8)',
    marginTop: 4,
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
  cardContent: {
    marginLeft: 12,
    flex: 1,
  },
  secondaryText: {
    color: '#666',
  },
  primaryValue: {
    fontWeight: '700',
    color: '#2196F3',
  },
  hintText: {
    color: '#666',
    marginTop: 2,
  },
  section: {
    marginTop: 8,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    marginBottom: 8,
  },
  sectionTitle: {
    fontWeight: '700',
  },
  emptyText: {
    textAlign: 'center',
    color: '#666',
    padding: 16,
  },
  quickLinks: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    gap: 12,
    marginTop: 16,
  },
  quickButton: {
    flex: 1,
    borderRadius: 8,
  },
});
