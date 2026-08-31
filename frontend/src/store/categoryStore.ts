import { create } from 'zustand';
import { categoriesApi, Category, CreateCategoryPayload } from '../api/categories';

interface CategoryState {
  categories: Category[];
  isLoading: boolean;
  error: string | null;
  fetchCategories: () => Promise<void>;
  createCategory: (data: CreateCategoryPayload) => Promise<Category>;
  getCategoriesByType: (type: 'income' | 'expense') => Category[];
}

export const useCategoryStore = create<CategoryState>((set, get) => ({
  categories: [],
  isLoading: false,
  error: null,

  fetchCategories: async () => {
    set({ isLoading: true, error: null });
    try {
      const categories = await categoriesApi.getAll();
      set({ categories, isLoading: false });
    } catch (error: any) {
      set({ error: error.message, isLoading: false });
    }
  },

  createCategory: async (data) => {
    const category = await categoriesApi.create(data);
    set({ categories: [...get().categories, category] });
    return category;
  },

  getCategoriesByType: (type) => {
    return get().categories.filter((c) => c.type === type);
  },
}));
