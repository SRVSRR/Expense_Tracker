import React, { useEffect, useState } from 'react';
import { View, StyleSheet, ScrollView, RefreshControl } from 'react-native';
import { Text, Surface, ActivityIndicator, ProgressBar, Divider } from 'react-native-paper';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Icon from '../../components/Icon';
import { budgetApi, BudgetRecommendation, CategoryAnalysis } from '../../api/budget';

const TAB_BAR_HEIGHT = 56;

export default function BudgetScreen() {
  const insets = useSafeAreaInsets();
  const [recommendations, setRecommendations] = useState<BudgetRecommendation[]>([]);
  const [categoryAnalysis, setCategoryAnalysis] = useState<CategoryAnalysis[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [recs, analysis] = await Promise.all([
        budgetApi.getRecommendations(),
        budgetApi.getCategoryAnalysis(),
      ]);
      setRecommendations(recs);
      setCategoryAnalysis(analysis);
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
          Budget
        </Text>
      </View>

      <Surface style={styles.card} elevation={2}>
        <View style={styles.cardHeader}>
          <Icon source="chart-pie" size={24} color="#2196F3" />
          <Text variant="titleMedium" style={styles.cardTitle}>
            Recommendations
          </Text>
        </View>
        {recommendations.length === 0 ? (
          <Text variant="bodyMedium" style={styles.emptyText}>
            No recommendations yet. Add more transactions to get budget suggestions.
          </Text>
        ) : (
          recommendations.slice(0, 5).map((rec, index) => (
            <View key={index} style={styles.recItem}>
              <View style={styles.recHeader}>
                <Text variant="bodyMedium" style={styles.recCategory}>
                  {rec.category}
                </Text>
                <Text variant="bodySmall" style={styles.secondaryText}>
                  {rec.trend === 'increasing' ? '\u2191' : rec.trend === 'decreasing' ? '\u2193' : '\u2192'}{' '}
                  {rec.trend}
                </Text>
              </View>
              <Text variant="bodySmall" style={styles.primaryValue}>
                Recommended: ${rec.recommended_limit.toFixed(2)}/month
              </Text>
              <Text variant="bodySmall" style={styles.hintText}>
                Historical avg: ${rec.historical_average.toFixed(2)}/month
              </Text>
            </View>
          ))
        )}
      </Surface>

      <Surface style={styles.card} elevation={2}>
        <View style={styles.cardHeader}>
          <Icon source="chart-bar" size={24} color="#4CAF50" />
          <Text variant="titleMedium" style={styles.cardTitle}>
            Category Spending
          </Text>
        </View>
        {categoryAnalysis.length === 0 ? (
          <Text variant="bodyMedium" style={styles.emptyText}>
            No spending data yet.
          </Text>
        ) : (
          categoryAnalysis.slice(0, 8).map((cat, index) => (
            <View key={index} style={styles.categoryItem}>
              <View style={styles.categoryHeader}>
                <Text variant="bodyMedium" style={styles.categoryName}>
                  {cat.category}
                </Text>
                <Text variant="bodySmall" style={styles.secondaryText}>
                  {cat.percentage_of_total.toFixed(1)}%
                </Text>
              </View>
              <ProgressBar
                progress={cat.percentage_of_total / 100}
                color="#2196F3"
                style={styles.progressBar}
              />
              <View style={styles.categoryStats}>
                <Text variant="bodySmall" style={styles.hintText}>
                  ${cat.total_spent.toFixed(2)} total
                </Text>
                <Text variant="bodySmall" style={styles.hintText}>
                  {cat.transaction_count} transactions
                </Text>
                <Text
                  variant="bodySmall"
                  style={cat.month_over_month_change >= 0 ? styles.negativeValue : styles.positiveValue}
                >
                  {cat.month_over_month_change >= 0 ? '+' : ''}
                  {cat.month_over_month_change.toFixed(1)}% vs last month
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
    marginBottom: 16,
  },
  cardTitle: {
    marginLeft: 8,
    fontWeight: '600',
  },
  emptyText: {
    textAlign: 'center',
    color: '#666',
    padding: 16,
  },
  secondaryText: {
    color: '#666',
  },
  hintText: {
    color: '#666',
    marginTop: 2,
  },
  primaryValue: {
    color: '#2196F3',
    marginTop: 4,
  },
  positiveValue: {
    fontWeight: '600',
    marginTop: 4,
    color: '#4CAF50',
  },
  negativeValue: {
    fontWeight: '600',
    marginTop: 4,
    color: '#F44336',
  },
  recItem: {
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#F0F0F0',
  },
  recHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  recCategory: {
    fontWeight: '600',
  },
  categoryItem: {
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#F0F0F0',
  },
  categoryHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  categoryName: {
    fontWeight: '600',
  },
  progressBar: {
    marginVertical: 8,
    height: 6,
    borderRadius: 3,
  },
  categoryStats: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
});
