import React, { useEffect, useState } from 'react';
import { View, StyleSheet, FlatList, RefreshControl, Alert } from 'react-native';
import { Text, FAB, Portal, Dialog, TextInput, Button } from 'react-native-paper';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useAccountStore } from '../../store/accountStore';
import AccountCard from '../../components/AccountCard';

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

  return (
    <View style={styles.container}>
      <View style={[styles.header, { paddingTop: insets.top + 16 }]}>
        <Text variant="headlineSmall" style={styles.title}>
          Accounts
        </Text>
      </View>

      <FlatList
        data={accounts}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <AccountCard
            account={item}
            onLongPress={() => handleDelete(item.id, item.name)}
          />
        )}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
        contentContainerStyle={[styles.list, { paddingBottom: TAB_BAR_HEIGHT + 80 }]}
        ListEmptyComponent={
          <Text variant="bodyMedium" style={styles.empty}>
            No accounts yet. Create one to get started!
          </Text>
        }
      />

      <FAB
        label="+"
        style={[styles.fab, { bottom: insets.bottom + TAB_BAR_HEIGHT + 16 }]}
        onPress={() => setDialogVisible(true)}
        color="#fff"
      />

      <Portal>
        <Dialog visible={dialogVisible} onDismiss={() => setDialogVisible(false)}>
          <Dialog.Title>New Account</Dialog.Title>
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
            <Button onPress={() => setDialogVisible(false)}>Cancel</Button>
            <Button onPress={handleAdd}>Create</Button>
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
    padding: 16,
    backgroundColor: '#2196F3',
  },
  title: {
    color: '#fff',
    fontWeight: '700',
  },
  list: {
    paddingTop: 8,
  },
  empty: {
    textAlign: 'center',
    color: '#666',
    marginTop: 40,
  },
  fab: {
    position: 'absolute',
    right: 16,
    backgroundColor: '#2196F3',
    borderRadius: 16,
  },
  dialogInput: {
    marginBottom: 12,
  },
});
