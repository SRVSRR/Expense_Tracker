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
      </View>

      {runway && (
        <Surface style={styles.card} elevation={2}>
          <View style={styles.cardHeader}>
            <Icon source="clock-outline" size={28} color="#2196F3" />
            <Text variant="titleMedium" style={styles.cardTitle}>
              Runway
            </Text>
          </View>
          <Text variant="displaySmall" style={styles.runwayDays}>
            {runway.days_until_zero} days
          </Text>
          <Text variant="bodyMedium" style={styles.secondaryText}>
            Until balance reaches $0
          </Text>
          <Divider style={styles.divider} />
          <View style={styles.statsRow}>
            <View style={styles.statItem}>
              <Text variant="bodySmall" style={styles.secondaryText}>
                Current Balance
              </Text>
              <Text variant="bodyLarge" style={styles.primaryValue}>
                ${runway.current_balance.toFixed(2)}
              </Text>
            </View>
            <View style={styles.statItem}>
              <Text variant="bodySmall" style={styles.secondaryText}>
                Daily Burn
              </Text>
              <Text variant="bodyLarge" style={styles.negativeValue}>
                ${runway.avg_daily_burn.toFixed(2)}/day
              </Text>
            </View>
          </View>
        </Surface>
      )}

      {cashflow && (
        <Surface style={styles.card} elevation={2}>
          <View style={styles.cardHeader}>
            <Icon source="trending-up" size={24} color="#4CAF50" />
            <Text variant="titleMedium" style={styles.cardTitle}>
              30-Day Cash Flow
            </Text>
          </View>
          <View style={styles.statsRow}>
            <View style={styles.statItem}>
              <Text variant="bodySmall" style={styles.secondaryText}>
                Projected Income
              </Text>
              <Text variant="titleMedium" style={styles.positiveValue}>
                +${cashflow.summary.total_income.toFixed(2)}
              </Text>
            </View>
            <View style={styles.statItem}>
              <Text variant="bodySmall" style={styles.secondaryText}>
                Projected Expenses
              </Text>
              <Text variant="titleMedium" style={styles.negativeValue}>
                -${cashflow.summary.total_expenses.toFixed(2)}
              </Text>
            </View>
          </View>
          <Divider style={styles.divider} />
          <View style={styles.centeredItem}>
            <Text variant="bodyMedium" style={styles.secondaryText}>
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

      <Surface style={styles.card} elevation={2}>
        <View style={styles.cardHeader}>
          <Icon source="alert-circle-outline" size={24} color="#FF9800" />
          <Text variant="titleMedium" style={styles.cardTitle}>
            Anomalies
          </Text>
        </View>
        {anomalies.length === 0 ? (
          <Text variant="bodyMedium" style={styles.emptyText}>
            No anomalies detected
          </Text>
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
                <Text variant="bodySmall" style={styles.hintText}>
                  {anomaly.category} • ${anomaly.amount.toFixed(2)} •{' '}
                  {anomaly.severity} severity
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
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  cardTitle: {
    marginLeft: 8,
    fontWeight: '600',
  },
  runwayDays: {
    fontWeight: '700',
    color: '#2196F3',
  },
  secondaryText: {
    color: '#666',
  },
  hintText: {
    color: '#666',
    marginTop: 2,
  },
  divider: {
    marginVertical: 16,
  },
  statsRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  statItem: {
    alignItems: 'center',
  },
  primaryValue: {
    fontWeight: '700',
    marginTop: 4,
    color: '#2196F3',
  },
  positiveValue: {
    fontWeight: '700',
    marginTop: 4,
    color: '#4CAF50',
  },
  negativeValue: {
    fontWeight: '700',
    marginTop: 4,
    color: '#F44336',
  },
  centeredItem: {
    alignItems: 'center',
  },
  emptyText: {
    textAlign: 'center',
    color: '#666',
    padding: 16,
  },
  anomalyItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#F0F0F0',
  },
  severityDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
    marginRight: 12,
  },
  anomalyInfo: {
    flex: 1,
  },
  anomalyDesc: {
    fontWeight: '600',
  },
});
