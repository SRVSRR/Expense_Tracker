import React from 'react';
import { View, StyleSheet } from 'react-native';
import { Text, Card } from 'react-native-paper';
import Icon from '../components/Icon';
import { Colors } from '../theme/colors';
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
      <View style={styles.content}>
        <View style={styles.iconBg}>
          <Icon source="wallet" size={24} color={Colors.primary} />
        </View>
        <View style={styles.info}>
          <Text variant="bodyLarge" style={styles.name}>
            {account.name}
          </Text>
          <Text variant="bodySmall" style={styles.currency}>
            {account.currency}
          </Text>
        </View>
        <Text variant="titleMedium" style={styles.balance}>
          {balance.toFixed(2)}
        </Text>
      </View>
    </Card>
  );
}

const styles = StyleSheet.create({
  card: {
    marginHorizontal: 16,
    marginBottom: 10,
    padding: 16,
    borderRadius: 12,
    backgroundColor: Colors.surfaceCard,
    elevation: 0,
  },
  content: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  iconBg: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: Colors.primarySurface,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 14,
  },
  info: {
    flex: 1,
  },
  name: {
    fontWeight: '600',
    color: Colors.textPrimary,
  },
  currency: {
    color: Colors.textTertiary,
    marginTop: 2,
  },
  balance: {
    fontWeight: '700',
    color: Colors.textPrimary,
  },
});
