import React from 'react';
import { View, StyleSheet } from 'react-native';
import { Text, Surface } from 'react-native-paper';
import Icon from './Icon';
import { Colors } from '../theme/colors';
import { UpcomingTransaction } from '../api/recurring';

interface Props {
  transaction: UpcomingTransaction;
}

export default function UpcomingCard({ transaction }: Props) {
  const date = new Date(transaction.expected_date);
  const now = new Date();
  const diffDays = Math.ceil((date.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));

  const dateLabel =
    diffDays === 0
      ? 'Today'
      : diffDays === 1
      ? 'Tomorrow'
      : diffDays <= 7
      ? `In ${diffDays} days`
      : date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });

  return (
    <Surface style={styles.card} elevation={0}>
      <View style={styles.row}>
        <View style={styles.iconBg}>
          <Icon source="repeat" size={16} color={Colors.tertiary} />
        </View>
        <View style={styles.details}>
          <Text variant="bodyMedium" style={styles.amount}>
            ${transaction.expected_amount.toFixed(2)}
          </Text>
          <Text variant="bodySmall" style={styles.meta}>
            {transaction.pattern} &middot; every {transaction.frequency} period{transaction.frequency !== 1 ? 's' : ''}
          </Text>
        </View>
        <View style={styles.dateBadge}>
          <Text variant="bodySmall" style={styles.dateLabel}>
            {dateLabel}
          </Text>
        </View>
      </View>
    </Surface>
  );
}

const styles = StyleSheet.create({
  card: {
    marginBottom: 6,
    padding: 12,
    borderRadius: 10,
    backgroundColor: Colors.surfaceCard,
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  iconBg: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: Colors.tertiarySurface,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 10,
  },
  details: {
    flex: 1,
  },
  amount: {
    fontWeight: '700',
    color: Colors.textPrimary,
  },
  meta: {
    color: Colors.textTertiary,
    marginTop: 2,
  },
  dateBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
    backgroundColor: Colors.surfaceElevated,
  },
  dateLabel: {
    color: Colors.textSecondary,
    fontWeight: '600',
  },
});
