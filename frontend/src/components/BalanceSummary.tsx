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
      <View style={styles.content}>
        <View style={styles.topRow}>
          <View>
            <Text variant="bodySmall" style={styles.label}>
              Total Balance
            </Text>
            <Text variant="headlineLarge" style={styles.amount}>
              ${totalBalance.toFixed(2)}
            </Text>
          </View>
          <View style={styles.iconCircle}>
            <Icon source="wallet" size={28} color="rgba(255,255,255,0.9)" />
          </View>
        </View>
        <View style={styles.bottomRow}>
          <View style={styles.accountBadge}>
            <Icon source="account" size={14} color="rgba(255,255,255,0.7)" />
            <Text variant="bodySmall" style={styles.accountCount}>
              {accounts.length} account{accounts.length !== 1 ? 's' : ''}
            </Text>
          </View>
        </View>
      </View>
    </Surface>
  );
}

const styles = StyleSheet.create({
  container: {
    marginHorizontal: 16,
    marginTop: 16,
    borderRadius: 16,
    backgroundColor: '#2196F3',
    overflow: 'hidden',
  },
  content: {
    padding: 20,
  },
  topRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  label: {
    color: 'rgba(255,255,255,0.7)',
  },
  amount: {
    color: '#fff',
    fontWeight: '700',
    marginTop: 4,
  },
  iconCircle: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: 'rgba(255,255,255,0.15)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  bottomRow: {
    marginTop: 14,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: 'rgba(255,255,255,0.15)',
  },
  accountBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  accountCount: {
    color: 'rgba(255,255,255,0.8)',
  },
});
