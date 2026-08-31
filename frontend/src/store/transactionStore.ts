import { create } from 'zustand';
import {
  transactionsApi,
  Transaction,
  CreateTransactionPayload,
  TransactionFilters,
} from '../api/transactions';

interface TransactionState {
  transactions: Transaction[];
  isLoading: boolean;
  error: string | null;
  filters: TransactionFilters;
  setFilters: (filters: TransactionFilters) => void;
  fetchTransactions: (filters?: TransactionFilters) => Promise<void>;
  createTransaction: (data: CreateTransactionPayload) => Promise<Transaction>;
  updateTransaction: (id: string, data: Partial<CreateTransactionPayload>) => Promise<Transaction>;
  deleteTransaction: (id: string) => Promise<void>;
}

export const useTransactionStore = create<TransactionState>((set, get) => ({
  transactions: [],
  isLoading: false,
  error: null,
  filters: { limit: 50, offset: 0 },

  setFilters: (filters) => set({ filters }),

  fetchTransactions: async (filters?: TransactionFilters) => {
    set({ isLoading: true, error: null });
    try {
      const activeFilters = filters || get().filters;
      const transactions = await transactionsApi.getAll(activeFilters);
      set({ transactions, isLoading: false });
    } catch (error: any) {
      set({ error: error.message, isLoading: false });
    }
  },

  createTransaction: async (data) => {
    const transaction = await transactionsApi.create(data);
    set({ transactions: [transaction, ...get().transactions] });
    return transaction;
  },

  updateTransaction: async (id, data) => {
    const transaction = await transactionsApi.update(id, data);
    set({
      transactions: get().transactions.map((t) => (t.id === id ? transaction : t)),
    });
    return transaction;
  },

  deleteTransaction: async (id) => {
    await transactionsApi.delete(id);
    set({ transactions: get().transactions.filter((t) => t.id !== id) });
  },
}));
