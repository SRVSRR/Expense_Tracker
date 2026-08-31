import { create } from 'zustand';
import {
  recurringApi,
  RecurringRule,
  UpcomingTransaction,
  CreateRecurringRulePayload,
} from '../api/recurring';

interface RecurringState {
  rules: RecurringRule[];
  upcoming: UpcomingTransaction[];
  isLoading: boolean;
  error: string | null;
  fetchRules: () => Promise<void>;
  fetchUpcoming: (days?: number) => Promise<void>;
  createRule: (data: CreateRecurringRulePayload) => Promise<RecurringRule>;
  deleteRule: (id: string) => Promise<void>;
}

export const useRecurringStore = create<RecurringState>((set, get) => ({
  rules: [],
  upcoming: [],
  isLoading: false,
  error: null,

  fetchRules: async () => {
    set({ isLoading: true, error: null });
    try {
      const rules = await recurringApi.getAll();
      set({ rules, isLoading: false });
    } catch (error: any) {
      set({ error: error.message, isLoading: false });
    }
  },

  fetchUpcoming: async (days?: number) => {
    set({ isLoading: true, error: null });
    try {
      const upcoming = await recurringApi.getUpcoming(days);
      set({ upcoming, isLoading: false });
    } catch (error: any) {
      set({ error: error.message, isLoading: false });
    }
  },

  createRule: async (data) => {
    const rule = await recurringApi.create(data);
    set({ rules: [...get().rules, rule] });
    return rule;
  },

  deleteRule: async (id) => {
    await recurringApi.delete(id);
    set({ rules: get().rules.filter((r) => r.id !== id) });
  },
}));
