import React from 'react';
import { StyleSheet } from 'react-native';
import { Card, Text } from 'react-native-paper';
import Icon from '../components/Icon';
import { Account } from '../api/accounts';

interface Props {
  account: Account;
  onPress?: () => void;
  onLongPress?: () => void;
}

export default function AccountCard({ account, onPress, onLongPress }: Props) {
  const balance = account.current_balance ?? account.initial_balance;

  return (
    <Card style={styles.card} onPress={onPress} onLongPress={onLongPress}>
      <Card.Content style={styles.content}>
        <Icon source="wallet" size={32} color="#2196F3" />
        <Text variant="titleMedium" style={styles.name}>
          {account.name}
        </Text>
        <Text variant="headlineSmall" style={styles.balance}>
          {account.currency} {balance.toFixed(2)}
        </Text>
        <Text variant="bodySmall" style={styles.currency}>
          {account.currency}
        </Text>
      </Card.Content>
    </Card>
  );
}

const styles = StyleSheet.create({
  card: {
    marginHorizontal: 16,
    marginVertical: 8,
    borderRadius: 16,
    backgroundColor: '#fff',
  },
  content: {
    alignItems: 'center',
    paddingVertical: 16,
  },
  name: {
    marginTop: 8,
    fontWeight: '600',
  },
  balance: {
    marginTop: 4,
    fontWeight: '700',
    color: '#2196F3',
  },
  currency: {
    color: '#666',
    marginTop: 2,
  },
});
