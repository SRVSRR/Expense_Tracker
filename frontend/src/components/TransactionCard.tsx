import React from 'react';
import { View, StyleSheet } from 'react-native';
import { Card, Text } from 'react-native-paper';
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

  return (
    <Card style={styles.card} onPress={onPress}>
      <Card.Content style={styles.content}>
        <View style={[styles.iconContainer, { backgroundColor: isIncome ? '#E8F5E9' : '#FFEBEE' }]}>
          <Icon source={icon} size={20} color={amountColor} />
        </View>
        <View style={styles.details}>
          <Text variant="bodyMedium" style={styles.description} numberOfLines={1}>
            {transaction.description}
          </Text>
          <Text variant="bodySmall" style={styles.category}>
            {transaction.category}
            {transaction.merchant ? ` • ${transaction.merchant}` : ''}
          </Text>
        </View>
        <View style={styles.amountContainer}>
          <Text variant="bodyLarge" style={[styles.amount, { color: amountColor }]}>
            {isIncome ? '+' : '-'}${transaction.amount.toFixed(2)}
          </Text>
          <Text variant="bodySmall" style={styles.date}>
            {new Date(transaction.date).toLocaleDateString()}
          </Text>
        </View>
      </Card.Content>
    </Card>
  );
}

const styles = StyleSheet.create({
  card: {
    marginHorizontal: 16,
    marginVertical: 4,
    borderRadius: 12,
    backgroundColor: '#fff',
  },
  content: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 8,
  },
  iconContainer: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  details: {
    flex: 1,
  },
  description: {
    fontWeight: '600',
  },
  category: {
    color: '#666',
    marginTop: 2,
  },
  amountContainer: {
    alignItems: 'flex-end',
  },
  amount: {
    fontWeight: '700',
  },
  date: {
    color: '#999',
    marginTop: 2,
  },
});
