import React, { useEffect, useState } from 'react';
import { View, StyleSheet, ScrollView, RefreshControl } from 'react-native';
import { Text, Surface, ActivityIndicator, ProgressBar, Divider } from 'react-native-paper';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Icon from '../../components/Icon';
import { Colors } from '../../theme/colors';
import { budgetApi, BudgetRecommendation, CategoryAnalysis } from '../../api/budget';

const TAB_BAR_HEIGHT = 52;

const trendIcons: Record<string, string> = {
  increasing: '\u2191',
  decreasing: '\u2193',
  stable: '\u2192',
};

const trendColors: Record<string, string> = {
  increasing: Colors.expense,
  decreasing: Colors.income,
  stable: Colors.textTertiary,
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
        <ActivityIndicator size="large" color={Colors.primary} />
        <Text variant="bodySmall" style={{ color: Colors.textTertiary, marginTop: 12 }}>
          Analyzing spending...
        </Text>
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={{ paddingBottom: TAB_BAR_HEIGHT + 16 }}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={Colors.primary} />}
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
      <Surface style={styles.card} elevation={0}>
        <View style={styles.cardHeader}>
          <View style={[styles.cardIconBg, { backgroundColor: Colors.primarySurface }]}>
            <Icon source="chart-pie" size={20} color={Colors.primary} />
          </View>
          <Text variant="titleMedium" style={styles.cardTitle}>
            Recommendations
          </Text>
        </View>
        {recommendations.length === 0 ? (
          <View style={styles.emptyState}>
            <Icon source="info" size={24} color={Colors.textDisabled} />
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
                  <Text style={[styles.trendIcon, { color: trendColors[rec.trend] || Colors.textTertiary }]}>
                    {trendIcons[rec.trend] || '\u2192'}
                  </Text>
                  <Text variant="bodySmall" style={[styles.trendText, { color: trendColors[rec.trend] || Colors.textTertiary }]}>
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
      <Surface style={styles.card} elevation={0}>
        <View style={styles.cardHeader}>
          <View style={[styles.cardIconBg, { backgroundColor: Colors.tertiarySurface }]}>
            <Icon source="chart-bar" size={20} color={Colors.tertiary} />
          </View>
          <Text variant="titleMedium" style={styles.cardTitle}>
            Category Spending
          </Text>
        </View>
        {categoryAnalysis.length === 0 ? (
          <View style={styles.emptyState}>
            <Icon source="info" size={24} color={Colors.textDisabled} />
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
                color={cat.percentage_of_total > 30 ? Colors.warning : Colors.primary}
                style={styles.progressBar}
              />
              <View style={styles.categoryFooter}>
                <Text variant="bodySmall" style={styles.categoryStat}>
                  ${cat.total_spent.toFixed(2)} &middot; {cat.transaction_count} txns
                </Text>
                <Text
                  variant="bodySmall"
                  style={{ fontWeight: '600', color: cat.month_over_month_change >= 0 ? Colors.expense : Colors.income }}
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
    backgroundColor: Colors.background,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: Colors.background,
  },
  header: {
    paddingHorizontal: 20,
    paddingBottom: 16,
    backgroundColor: Colors.primary,
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
    backgroundColor: Colors.surfaceCard,
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
    color: Colors.textPrimary,
  },
  emptyState: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    padding: 12,
  },
  emptyText: {
    color: Colors.textTertiary,
    flex: 1,
  },
  recItem: {
    paddingVertical: 14,
    borderTopWidth: 1,
    borderTopColor: Colors.divider,
  },
  recHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  recCategory: {
    fontWeight: '700',
    color: Colors.textPrimary,
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
    color: Colors.textTertiary,
    marginBottom: 2,
  },
  recAmount: {
    fontWeight: '700',
    color: Colors.primary,
  },
  recPeriod: {
    fontWeight: '400',
    color: Colors.textTertiary,
  },
  recHistorical: {
    color: Colors.textSecondary,
    fontWeight: '600',
  },
  categoryItem: {
    paddingVertical: 14,
    borderTopWidth: 1,
    borderTopColor: Colors.divider,
  },
  categoryHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
  categoryName: {
    fontWeight: '700',
    color: Colors.textPrimary,
  },
  categoryPercent: {
    fontWeight: '600',
    color: Colors.primary,
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
    color: Colors.textTertiary,
  },
});
