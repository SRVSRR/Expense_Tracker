import React from 'react';
import { View, StyleSheet } from 'react-native';
import { Text, Surface } from 'react-native-paper';
import Icon from '../components/Icon';
import { Account } from '../api/accounts';

interface Props {
  accounts: Account[];
}

export default function BalanceSummary({ accounts }: Props) {
  const totalBalance = accounts.reduce((sum, acc) => {
    return sum + (acc.current_balance ?? acc.initial_balance);
  }, 0);

  return (
    <Surface style={styles.container} elevation={3}>
      <Text variant="bodyMedium" style={styles.label}>
        Total Balance
      </Text>
      <Text variant="headlineLarge" style={styles.amount}>
        ${totalBalance.toFixed(2)}
      </Text>
      <View style={styles.row}>
        <View style={styles.stat}>
          <Icon source="wallet" size={16} color="#2196F3" />
          <Text variant="bodySmall" style={styles.statText}>
            {accounts.length} account{accounts.length !== 1 ? 's' : ''}
          </Text>
        </View>
      </View>
    </Surface>
  );
}

const styles = StyleSheet.create({
  container: {
    margin: 16,
    padding: 20,
    borderRadius: 16,
    backgroundColor: '#2196F3',
  },
  label: {
    color: 'rgba(255,255,255,0.8)',
    textAlign: 'center',
  },
  amount: {
    color: '#fff',
    fontWeight: '700',
    textAlign: 'center',
    marginTop: 4,
    marginBottom: 12,
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'center',
  },
  stat: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  statText: {
    color: 'rgba(255,255,255,0.8)',
  },
});
