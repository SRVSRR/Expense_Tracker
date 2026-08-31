import React from 'react';
import { View, StyleSheet } from 'react-native';
import { Text, Card } from 'react-native-paper';
import Icon from '../components/Icon';
import { Transaction } from '../api/transactions';

interface Props {
  transaction: Transaction;
  onPress?: () => void;
}

export default function TransactionCard({ transaction, onPress }: Props) {
  const isIncome = transaction.type === 'income';
  const amountColor = isIncome ? '#4CAF50' : '#F44336';
  const icon = isIncome ? 'arrow-down-bold' : 'arrow-up-bold';
  const iconBg = isIncome ? '#E8F5E9' : '#FFEBEE';

  return (
    <Card style={styles.card} onPress={onPress}>
      <View style={styles.content}>
        <View style={[styles.iconContainer, { backgroundColor: iconBg }]}>
          <Icon source={icon} size={16} color={amountColor} />
        </View>
        <View style={styles.details}>
          <Text variant="bodyMedium" style={styles.description} numberOfLines={1}>
            {transaction.description}
          </Text>
          <Text variant="bodySmall" style={styles.meta}>
            {transaction.category}
            {transaction.merchant ? ` \u00B7 ${transaction.merchant}` : ''}
          </Text>
        </View>
        <View style={styles.amountContainer}>
          <Text variant="bodyLarge" style={[styles.amount, { color: amountColor }]}>
            {isIncome ? '+' : '-'}${transaction.amount.toFixed(2)}
          </Text>
          <Text variant="bodySmall" style={styles.date}>
            {new Date(transaction.date).toLocaleDateString('en-US', {
              month: 'short',
              day: 'numeric',
            })}
          </Text>
        </View>
      </View>
    </Card>
  );
}

const styles = StyleSheet.create({
  card: {
    marginHorizontal: 16,
    marginBottom: 2,
    paddingVertical: 4,
    paddingHorizontal: 0,
    borderRadius: 0,
    backgroundColor: 'transparent',
  },
  content: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 10,
    paddingHorizontal: 4,
  },
  iconContainer: {
    width: 38,
    height: 38,
    borderRadius: 19,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  details: {
    flex: 1,
  },
  description: {
    fontWeight: '600',
    color: '#333',
  },
  meta: {
    color: '#999',
    marginTop: 2,
  },
  amountContainer: {
    alignItems: 'flex-end',
  },
  amount: {
    fontWeight: '700',
  },
  date: {
    color: '#BBB',
    marginTop: 2,
  },
});
