import React, { useEffect, useState } from 'react';
import { View, StyleSheet, ScrollView, RefreshControl } from 'react-native';
import { Text, Surface, ActivityIndicator, ProgressBar, Divider } from 'react-native-paper';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Icon from '../../components/Icon';
import { budgetApi, BudgetRecommendation, CategoryAnalysis } from '../../api/budget';

const TAB_BAR_HEIGHT = 52;

const trendIcons: Record<string, string> = {
  increasing: '\u2191',
  decreasing: '\u2193',
  stable: '\u2192',
};

const trendColors: Record<string, string> = {
  increasing: '#F44336',
  decreasing: '#4CAF50',
  stable: '#999',
};

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
        <Text variant="bodySmall" style={{ color: '#999', marginTop: 12 }}>
          Analyzing spending...
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
          Budget
        </Text>
        <Text variant="bodySmall" style={styles.subtitle}>
          Smart spending recommendations
        </Text>
      </View>

      {/* Recommendations */}
      <Surface style={styles.card} elevation={2}>
        <View style={styles.cardHeader}>
          <View style={[styles.cardIconBg, { backgroundColor: '#E3F2FD' }]}>
            <Icon source="chart-pie" size={20} color="#2196F3" />
          </View>
          <Text variant="titleMedium" style={styles.cardTitle}>
            Recommendations
          </Text>
        </View>
        {recommendations.length === 0 ? (
          <View style={styles.emptyState}>
            <Icon source="info" size={24} color="#CCC" />
            <Text variant="bodyMedium" style={styles.emptyText}>
              Add more transactions to get budget suggestions
            </Text>
          </View>
        ) : (
          recommendations.slice(0, 5).map((rec, index) => (
            <View key={index} style={styles.recItem}>
              <View style={styles.recHeader}>
                <Text variant="bodyMedium" style={styles.recCategory}>
                  {rec.category}
                </Text>
                <View style={styles.trendBadge}>
                  <Text style={[styles.trendIcon, { color: trendColors[rec.trend] || '#999' }]}>
                    {trendIcons[rec.trend] || '\u2192'}
                  </Text>
                  <Text variant="bodySmall" style={[styles.trendText, { color: trendColors[rec.trend] || '#999' }]}>
                    {rec.trend}
                  </Text>
                </View>
              </View>
              <View style={styles.recValues}>
                <View>
                  <Text variant="bodySmall" style={styles.recLabel}>
                    Recommended
                  </Text>
                  <Text variant="bodyLarge" style={styles.recAmount}>
                    ${rec.recommended_limit.toFixed(2)}
                    <Text variant="bodySmall" style={styles.recPeriod}>/month</Text>
                  </Text>
                </View>
                <View>
                  <Text variant="bodySmall" style={styles.recLabel}>
                    Historical avg
                  </Text>
                  <Text variant="bodySmall" style={styles.recHistorical}>
                    ${rec.historical_average.toFixed(2)}/month
                  </Text>
                </View>
              </View>
            </View>
          ))
        )}
      </Surface>

      {/* Category Spending */}
      <Surface style={styles.card} elevation={2}>
        <View style={styles.cardHeader}>
          <View style={[styles.cardIconBg, { backgroundColor: '#E8F5E9' }]}>
            <Icon source="chart-bar" size={20} color="#4CAF50" />
          </View>
          <Text variant="titleMedium" style={styles.cardTitle}>
            Category Spending
          </Text>
        </View>
        {categoryAnalysis.length === 0 ? (
          <View style={styles.emptyState}>
            <Icon source="info" size={24} color="#CCC" />
            <Text variant="bodyMedium" style={styles.emptyText}>
              No spending data yet
            </Text>
          </View>
        ) : (
          categoryAnalysis.slice(0, 8).map((cat, index) => (
            <View key={index} style={styles.categoryItem}>
              <View style={styles.categoryHeader}>
                <Text variant="bodyMedium" style={styles.categoryName}>
                  {cat.category}
                </Text>
                <Text variant="bodySmall" style={styles.categoryPercent}>
                  {cat.percentage_of_total.toFixed(1)}%
                </Text>
              </View>
              <ProgressBar
                progress={cat.percentage_of_total / 100}
                color={cat.percentage_of_total > 30 ? '#FF9800' : '#2196F3'}
                style={styles.progressBar}
              />
              <View style={styles.categoryFooter}>
                <Text variant="bodySmall" style={styles.categoryStat}>
                  ${cat.total_spent.toFixed(2)} &middot; {cat.transaction_count} txns
                </Text>
                <Text
                  variant="bodySmall"
                  style={cat.month_over_month_change >= 0 ? styles.changeNeg : styles.changePos}
                >
                  {cat.month_over_month_change >= 0 ? '+' : ''}
                  {cat.month_over_month_change.toFixed(1)}%
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
  emptyState: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    padding: 12,
  },
  emptyText: {
    color: '#999',
    flex: 1,
  },
  recItem: {
    paddingVertical: 14,
    borderTopWidth: 1,
    borderTopColor: '#F5F5F5',
  },
  recHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  recCategory: {
    fontWeight: '700',
    color: '#333',
  },
  trendBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  trendIcon: {
    fontSize: 14,
    fontWeight: '700',
  },
  trendText: {
    fontWeight: '600',
  },
  recValues: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  recLabel: {
    color: '#999',
    marginBottom: 2,
  },
  recAmount: {
    fontWeight: '700',
    color: '#2196F3',
  },
  recPeriod: {
    fontWeight: '400',
    color: '#999',
  },
  recHistorical: {
    color: '#666',
    fontWeight: '600',
  },
  categoryItem: {
    paddingVertical: 14,
    borderTopWidth: 1,
    borderTopColor: '#F5F5F5',
  },
  categoryHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
  categoryName: {
    fontWeight: '700',
    color: '#333',
  },
  categoryPercent: {
    fontWeight: '600',
    color: '#2196F3',
  },
  progressBar: {
    height: 6,
    borderRadius: 3,
    marginBottom: 6,
  },
  categoryFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  categoryStat: {
    color: '#999',
  },
  changeNeg: {
    fontWeight: '600',
    color: '#F44336',
  },
  changePos: {
    fontWeight: '600',
    color: '#4CAF50',
  },
});
