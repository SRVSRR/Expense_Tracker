import { create } from 'zustand';
import { accountsApi, Account, CreateAccountPayload } from '../api/accounts';

interface AccountState {
  accounts: Account[];
  selectedAccount: Account | null;
  isLoading: boolean;
  error: string | null;
  fetchAccounts: () => Promise<void>;
  selectAccount: (account: Account | null) => void;
  createAccount: (data: CreateAccountPayload) => Promise<Account>;
  updateAccount: (id: string, data: Partial<CreateAccountPayload>) => Promise<Account>;
  deleteAccount: (id: string) => Promise<void>;
}

export const useAccountStore = create<AccountState>((set, get) => ({
  accounts: [],
  selectedAccount: null,
  isLoading: false,
  error: null,

  fetchAccounts: async () => {
    set({ isLoading: true, error: null });
    try {
      const accounts = await accountsApi.getAll();
      set({ accounts, isLoading: false });
    } catch (error: any) {
      set({ error: error.message, isLoading: false });
    }
  },

  selectAccount: (account) => set({ selectedAccount: account }),

  createAccount: async (data) => {
    const account = await accountsApi.create(data);
    set({ accounts: [...get().accounts, account] });
    return account;
  },

  updateAccount: async (id, data) => {
    const account = await accountsApi.update(id, data);
    set({
      accounts: get().accounts.map((a) => (a.id === id ? account : a)),
    });
    return account;
  },

  deleteAccount: async (id) => {
    await accountsApi.delete(id);
    set({ accounts: get().accounts.filter((a) => a.id !== id) });
  },
}));
