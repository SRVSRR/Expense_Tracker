import { create } from 'zustand';
import {
  Transaction,
  CreateTransactionPayload,
  TransactionFilters,
} from '../api/transactions';
import { transactionsApi } from '../api/transactions';
import {
  insertLocal,
  getLocalTransactions,
  deleteLocal,
  LocalTransaction,
} from '../db/localDb';
import { syncPendingTransactions } from '../services/syncService';
import { useAuthStore } from './authStore';
import { generateUUID } from '../utils/uuid';

interface TransactionState {
  transactions: LocalTransaction[];
  isLoading: boolean;
  error: string | null;
  filters: TransactionFilters;
  isOnline: boolean;
  setFilters: (filters: TransactionFilters) => void;
  setIsOnline: (online: boolean) => void;
  fetchTransactions: (filters?: TransactionFilters) => Promise<void>;
  createTransaction: (data: CreateTransactionPayload) => Promise<LocalTransaction>;
  updateTransaction: (id: string, data: Partial<CreateTransactionPayload>) => Promise<Transaction>;
  deleteTransaction: (id: string) => Promise<void>;
  sync: () => Promise<void>;
}

export const useTransactionStore = create<TransactionState>((set, get) => ({
  transactions: [],
  isLoading: false,
  error: null,
  filters: { limit: 50, offset: 0 },
  isOnline: true,

  setFilters: (filters) => set({ filters }),
  setIsOnline: (online) => set({ isOnline: online }),

  fetchTransactions: async (filters?: TransactionFilters) => {
    set({ isLoading: true, error: null });
    try {
      const userId = useAuthStore.getState().user?.id;
      if (!userId) throw new Error('Not authenticated');

      const activeFilters = filters || get().filters;

      // Local-first: read from SQLite immediately
      const localTxs = await getLocalTransactions(userId, {
        type: activeFilters.type,
        limit: activeFilters.limit,
        offset: activeFilters.offset,
      });
      set({ transactions: localTxs, isLoading: false });

      // Background sync: push pending, pull fresh
      syncPendingTransactions(userId).then(({ pushed }) => {
        if (pushed > 0 || get().transactions.length === 0) {
          // Re-fetch after sync if something was pushed
          getLocalTransactions(userId, {
            type: activeFilters.type,
            limit: activeFilters.limit,
            offset: activeFilters.offset,
          }).then((txs) => set({ transactions: txs }));
        }
      }).catch(() => {});
    } catch (error: any) {
      set({ error: error.message, isLoading: false });
    }
  },

  createTransaction: async (data) => {
    const userId = useAuthStore.getState().user?.id;
    if (!userId) throw new Error('Not authenticated');

    const localId = generateUUID();
    const now = new Date().toISOString();
    const localTx: LocalTransaction = {
      id: localId,
      user_id: userId,
      account_id: data.account_id,
      type: data.type,
      amount: data.amount,
      category: data.category,
      description: data.description,
      merchant: data.merchant,
      date: data.date,
      is_recurring: data.is_recurring || 0,
      created_at: now,
      updated_at: now,
      sync_status: 'pending',
    };

    // Write to local DB first (instant)
    await insertLocal(localTx);

    // Update local state immediately
    set({ transactions: [localTx, ...get().transactions] });

    // Try to push to backend in background
    transactionsApi.create(data).then((remoteTx) => {
      // If backend accepted it, mark as synced by re-fetching
      getLocalTransactions(userId).then((txs) => set({ transactions: txs }));
    }).catch(() => {
      // Offline — stays pending, will sync later
    });

    return localTx;
  },

  updateTransaction: async (id, data) => {
    const transaction = await transactionsApi.update(id, data);
    const userId = useAuthStore.getState().user?.id;
    if (userId) {
      const txs = await getLocalTransactions(userId);
      set({ transactions: txs });
    }
    return transaction;
  },

  deleteTransaction: async (id) => {
    await transactionsApi.delete(id);
    await deleteLocal(id);
    const userId = useAuthStore.getState().user?.id;
    if (userId) {
      const txs = await getLocalTransactions(userId);
      set({ transactions: txs });
    }
  },

  sync: async () => {
    const userId = useAuthStore.getState().user?.id;
    if (!userId) return;
    await syncPendingTransactions(userId);
    const activeFilters = get().filters;
    const txs = await getLocalTransactions(userId, {
      type: activeFilters.type,
      limit: activeFilters.limit,
      offset: activeFilters.offset,
    });
    set({ transactions: txs });
  },
}));
