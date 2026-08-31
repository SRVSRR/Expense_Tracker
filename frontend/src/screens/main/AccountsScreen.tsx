import React, { useEffect, useState } from 'react';
import { View, StyleSheet, FlatList, RefreshControl, Alert, TouchableOpacity } from 'react-native';
import { Text, FAB, Portal, Dialog, TextInput, Button, Surface } from 'react-native-paper';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Icon from '../../components/Icon';
import { useAccountStore } from '../../store/accountStore';

const TAB_BAR_HEIGHT = 56;

export default function AccountsScreen() {
  const insets = useSafeAreaInsets();
  const { accounts, isLoading, fetchAccounts, createAccount, deleteAccount } = useAccountStore();
  const [refreshing, setRefreshing] = useState(false);
  const [dialogVisible, setDialogVisible] = useState(false);
  const [newName, setNewName] = useState('');
  const [newCurrency, setNewCurrency] = useState('USD');
  const [newBalance, setNewBalance] = useState('');

  useEffect(() => {
    fetchAccounts();
  }, []);

  const onRefresh = async () => {
    setRefreshing(true);
    await fetchAccounts();
    setRefreshing(false);
  };

  const handleAdd = async () => {
    if (!newName || !newBalance) {
      Alert.alert('Error', 'Please fill in all fields');
      return;
    }
    try {
      await createAccount({
        name: newName,
        currency: newCurrency,
        initial_balance: parseFloat(newBalance),
      });
      setDialogVisible(false);
      setNewName('');
      setNewCurrency('USD');
      setNewBalance('');
    } catch (error: any) {
      Alert.alert('Error', error.response?.data?.detail || 'Failed to create account');
    }
  };

  const handleDelete = (id: string, name: string) => {
    Alert.alert('Delete Account', `Are you sure you want to delete "${name}"?`, [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Delete',
        style: 'destructive',
        onPress: async () => {
          try {
            await deleteAccount(id);
          } catch {}
        },
      },
    ]);
  };

  const totalBalance = accounts.reduce(
    (sum, acc) => sum + (acc.current_balance ?? acc.initial_balance),
    0
  );

  const renderAccount = ({ item }: { item: any }) => {
    const balance = item.current_balance ?? item.initial_balance;
    return (
      <TouchableOpacity
        onLongPress={() => handleDelete(item.id, item.name)}
        activeOpacity={0.7}
      >
        <Surface style={styles.accountCard} elevation={1}>
          <View style={styles.accountIconBg}>
            <Icon source="wallet" size={22} color="#2196F3" />
          </View>
          <View style={styles.accountInfo}>
            <Text variant="bodyLarge" style={styles.accountName}>
              {item.name}
            </Text>
            <Text variant="bodySmall" style={styles.accountCurrency}>
              {item.currency}
            </Text>
          </View>
          <Text variant="titleMedium" style={styles.accountBalance}>
            {item.currency} {balance.toFixed(2)}
          </Text>
        </Surface>
      </TouchableOpacity>
    );
  };

  return (
    <View style={styles.container}>
      <View style={[styles.header, { paddingTop: insets.top + 16 }]}>
        <Text variant="headlineSmall" style={styles.title}>
          Accounts
        </Text>
        {accounts.length > 0 && (
          <Text variant="bodySmall" style={styles.subtitle}>
            {accounts.length} account{accounts.length !== 1 ? 's' : ''} &middot; Total: ${totalBalance.toFixed(2)}
          </Text>
        )}
      </View>

      <FlatList
        data={accounts}
        keyExtractor={(item) => item.id}
        renderItem={renderAccount}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
        contentContainerStyle={[styles.list, { paddingBottom: TAB_BAR_HEIGHT + 80 }]}
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <View style={styles.emptyIconBg}>
              <Icon source="wallet" size={40} color="#CCC" />
            </View>
            <Text variant="bodyLarge" style={styles.emptyTitle}>
              No accounts yet
            </Text>
            <Text variant="bodySmall" style={styles.emptyHint}>
              Create an account to start tracking{'\n'}your balances
            </Text>
          </View>
        }
      />

      <FAB
        icon="plus-circle"
        label="New Account"
        style={[styles.fab, { bottom: insets.bottom + TAB_BAR_HEIGHT + 16 }]}
        onPress={() => setDialogVisible(true)}
        color="#fff"
      />

      <Portal>
        <Dialog visible={dialogVisible} onDismiss={() => setDialogVisible(false)} style={styles.dialog}>
          <Dialog.Title style={styles.dialogTitle}>New Account</Dialog.Title>
          <Dialog.Content>
            <TextInput
              label="Account Name"
              value={newName}
              onChangeText={setNewName}
              mode="outlined"
              style={styles.dialogInput}
            />
            <TextInput
              label="Currency"
              value={newCurrency}
              onChangeText={setNewCurrency}
              mode="outlined"
              style={styles.dialogInput}
              disabled
            />
            <TextInput
              label="Initial Balance"
              value={newBalance}
              onChangeText={setNewBalance}
              mode="outlined"
              keyboardType="decimal-pad"
              left={<TextInput.Affix text="$" />}
              style={styles.dialogInput}
            />
          </Dialog.Content>
          <Dialog.Actions>
            <Button onPress={() => setDialogVisible(false)} textColor="#666">
              Cancel
            </Button>
            <Button onPress={handleAdd} buttonColor="#2196F3" textColor="#fff">
              Create
            </Button>
          </Dialog.Actions>
        </Dialog>
      </Portal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
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
  list: {
    paddingTop: 12,
  },
  accountCard: {
    flexDirection: 'row',
    alignItems: 'center',
    marginHorizontal: 16,
    marginBottom: 10,
    padding: 16,
    borderRadius: 12,
    backgroundColor: '#fff',
  },
  accountIconBg: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#E3F2FD',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 14,
  },
  accountInfo: {
    flex: 1,
  },
  accountName: {
    fontWeight: '600',
    color: '#333',
  },
  accountCurrency: {
    color: '#999',
    marginTop: 2,
  },
  accountBalance: {
    fontWeight: '700',
    color: '#333',
  },
  emptyContainer: {
    alignItems: 'center',
    paddingTop: 48,
    paddingHorizontal: 32,
  },
  emptyIconBg: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: '#F0F0F0',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
  },
  emptyTitle: {
    color: '#666',
    fontWeight: '600',
    marginBottom: 8,
  },
  emptyHint: {
    color: '#999',
    textAlign: 'center',
    lineHeight: 20,
  },
  fab: {
    position: 'absolute',
    right: 16,
    backgroundColor: '#2196F3',
    borderRadius: 14,
  },
  dialog: {
    borderRadius: 16,
  },
  dialogTitle: {
    fontWeight: '700',
  },
  dialogInput: {
    marginBottom: 12,
  },
});
