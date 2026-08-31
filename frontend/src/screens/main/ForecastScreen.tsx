import React, { useEffect, useState } from 'react';
import { View, StyleSheet, ScrollView, RefreshControl } from 'react-native';
import { Text, Surface, ActivityIndicator, Divider } from 'react-native-paper';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Icon from '../../components/Icon';
import { forecastApi, CashflowForecast, RunwayData, Anomaly } from '../../api/forecast';

const TAB_BAR_HEIGHT = 56;

export default function ForecastScreen() {
  const insets = useSafeAreaInsets();
  const [cashflow, setCashflow] = useState<CashflowForecast | null>(null);
  const [runway, setRunway] = useState<RunwayData | null>(null);
  const [anomalies, setAnomalies] = useState<Anomaly[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [cf, rw, an] = await Promise.all([
        forecastApi.getCashflow(30),
        forecastApi.getRunway(),
        forecastApi.getAnomalies(),
      ]);
      setCashflow(cf);
      setRunway(rw);
      setAnomalies(an);
    } catch {}
    setIsLoading(false);
  };

  useEffect(() => {
    loadData();
  }, []);

  const onRefresh = async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
  };

  if (isLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#2196F3" />
        <Text variant="bodySmall" style={{ color: '#999', marginTop: 12 }}>
          Loading forecast...
        </Text>
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={{ paddingBottom: TAB_BAR_HEIGHT + 16 }}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
    >
      <View style={[styles.header, { paddingTop: insets.top + 16 }]}>
        <Text variant="headlineSmall" style={styles.title}>
          Forecast
        </Text>
        <Text variant="bodySmall" style={styles.subtitle}>
          Projected financial outlook
        </Text>
      </View>

      {/* Runway Card */}
      {runway && (
        <Surface style={[styles.card, styles.runwayCard]} elevation={2}>
          <View style={styles.runwayHeader}>
            <View style={styles.runwayIconBg}>
              <Icon source="clock-outline" size={24} color="#fff" />
            </View>
            <View>
              <Text variant="bodySmall" style={styles.runwayLabel}>
                Financial Runway
              </Text>
              <Text variant="displaySmall" style={styles.runwayDays}>
                {runway.days_until_zero}
                <Text variant="bodyMedium" style={styles.runwayUnit}> days</Text>
              </Text>
            </View>
          </View>
          <Divider style={styles.lightDivider} />
          <View style={styles.statsRow}>
            <View style={styles.statItem}>
              <Text variant="bodySmall" style={styles.statLabel}>
                Balance
              </Text>
              <Text variant="bodyLarge" style={styles.statValue}>
                ${runway.current_balance.toFixed(2)}
              </Text>
            </View>
            <View style={styles.statDivider} />
            <View style={styles.statItem}>
              <Text variant="bodySmall" style={styles.statLabel}>
                Daily Burn
              </Text>
              <Text variant="bodyLarge" style={styles.statNeg}>
                ${runway.avg_daily_burn.toFixed(2)}/day
              </Text>
            </View>
          </View>
        </Surface>
      )}

      {/* Cash Flow Card */}
      {cashflow && (
        <Surface style={styles.card} elevation={2}>
          <View style={styles.cardHeader}>
            <View style={[styles.cardIconBg, { backgroundColor: '#E8F5E9' }]}>
              <Icon source="trending-up" size={20} color="#4CAF50" />
            </View>
            <Text variant="titleMedium" style={styles.cardTitle}>
              30-Day Cash Flow
            </Text>
          </View>
          <View style={styles.cashflowRow}>
            <View style={styles.cashflowItem}>
              <Text variant="bodySmall" style={styles.cashflowLabel}>
                Income
              </Text>
              <Text variant="titleMedium" style={styles.positiveValue}>
                +${cashflow.summary.total_income.toFixed(2)}
              </Text>
            </View>
            <View style={styles.cashflowDivider} />
            <View style={styles.cashflowItem}>
              <Text variant="bodySmall" style={styles.cashflowLabel}>
                Expenses
              </Text>
              <Text variant="titleMedium" style={styles.negativeValue}>
                -${cashflow.summary.total_expenses.toFixed(2)}
              </Text>
            </View>
          </View>
          <Divider style={styles.divider} />
          <View style={styles.netRow}>
            <Text variant="bodyMedium" style={styles.netLabel}>
              Net Change
            </Text>
            <Text
              variant="titleLarge"
              style={cashflow.summary.net_change >= 0 ? styles.positiveValue : styles.negativeValue}
            >
              {cashflow.summary.net_change >= 0 ? '+' : ''}$
              {cashflow.summary.net_change.toFixed(2)}
            </Text>
          </View>
        </Surface>
      )}

      {/* Anomalies Card */}
      <Surface style={styles.card} elevation={2}>
        <View style={styles.cardHeader}>
          <View style={[styles.cardIconBg, { backgroundColor: '#FFF3E0' }]}>
            <Icon source="alert-circle-outline" size={20} color="#FF9800" />
          </View>
          <Text variant="titleMedium" style={styles.cardTitle}>
            Anomalies
          </Text>
        </View>
        {anomalies.length === 0 ? (
          <View style={styles.emptyAnomaly}>
            <Icon source="check-circle" size={28} color="#4CAF50" />
            <Text variant="bodyMedium" style={styles.emptyAnomalyText}>
              All clear — no unusual spending detected
            </Text>
          </View>
        ) : (
          anomalies.slice(0, 5).map((anomaly) => (
            <View key={anomaly.id} style={styles.anomalyItem}>
              <View
                style={[
                  styles.severityDot,
                  {
                    backgroundColor:
                      anomaly.severity === 'high'
                        ? '#F44336'
                        : anomaly.severity === 'medium'
                        ? '#FF9800'
                        : '#FFC107',
                  },
                ]}
              />
              <View style={styles.anomalyInfo}>
                <Text variant="bodyMedium" style={styles.anomalyDesc}>
                  {anomaly.description}
                </Text>
                <Text variant="bodySmall" style={styles.anomalyMeta}>
                  {anomaly.category} &middot; ${anomaly.amount.toFixed(2)} &middot;{' '}
                  {anomaly.severity}
                </Text>
              </View>
            </View>
          ))
        )}
      </Surface>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F5',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
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
  card: {
    marginHorizontal: 16,
    marginTop: 12,
    padding: 18,
    borderRadius: 12,
    backgroundColor: '#fff',
  },
  runwayCard: {
    backgroundColor: '#2196F3',
  },
  runwayHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 14,
  },
  runwayIconBg: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: 'rgba(255,255,255,0.2)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  runwayLabel: {
    color: 'rgba(255,255,255,0.7)',
  },
  runwayDays: {
    fontWeight: '700',
    color: '#fff',
  },
  runwayUnit: {
    color: 'rgba(255,255,255,0.8)',
    fontWeight: '400',
  },
  lightDivider: {
    backgroundColor: 'rgba(255,255,255,0.2)',
    marginVertical: 14,
  },
  statsRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  statItem: {
    flex: 1,
    alignItems: 'center',
  },
  statDivider: {
    width: 1,
    height: 28,
    backgroundColor: 'rgba(255,255,255,0.2)',
  },
  statLabel: {
    color: 'rgba(255,255,255,0.7)',
  },
  statValue: {
    fontWeight: '700',
    color: '#fff',
    marginTop: 2,
  },
  statNeg: {
    fontWeight: '700',
    color: '#FFCDD2',
    marginTop: 2,
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 14,
    gap: 10,
  },
  cardIconBg: {
    width: 36,
    height: 36,
    borderRadius: 18,
    justifyContent: 'center',
    alignItems: 'center',
  },
  cardTitle: {
    fontWeight: '700',
    color: '#333',
  },
  cashflowRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  cashflowItem: {
    flex: 1,
    alignItems: 'center',
  },
  cashflowLabel: {
    color: '#666',
  },
  cashflowDivider: {
    width: 1,
    height: 28,
    backgroundColor: '#E8E8E8',
  },
  divider: {
    marginVertical: 12,
  },
  netRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  netLabel: {
    color: '#333',
    fontWeight: '600',
  },
  positiveValue: {
    fontWeight: '700',
    color: '#4CAF50',
  },
  negativeValue: {
    fontWeight: '700',
    color: '#F44336',
  },
  emptyAnomaly: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    padding: 8,
  },
  emptyAnomalyText: {
    color: '#666',
    flex: 1,
  },
  anomalyItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#F5F5F5',
  },
  severityDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 12,
  },
  anomalyInfo: {
    flex: 1,
  },
  anomalyDesc: {
    fontWeight: '600',
    color: '#333',
  },
  anomalyMeta: {
    color: '#999',
    marginTop: 2,
  },
});
