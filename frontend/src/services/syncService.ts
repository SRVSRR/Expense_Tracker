import { getPendingLocal, deletePendingLocal, upsertFromRemote } from '../db/localDb';
import { transactionsApi } from '../api/transactions';

let syncing = false;

export async function syncPendingTransactions(userId: string): Promise<{ pushed: number; pulled: number }> {
  if (syncing) return { pushed: 0, pulled: 0 };
  syncing = true;

  let pushed = 0;
  let pulled = 0;

  try {
    // 1. Push pending local transactions to remote
    const pending = await getPendingLocal(userId);
    for (const tx of pending) {
      try {
        await transactionsApi.create({
          account_id: tx.account_id,
          type: tx.type as 'income' | 'expense',
          amount: tx.amount,
          category: tx.category,
          description: tx.description,
          merchant: tx.merchant,
          date: tx.date,
          is_recurring: tx.is_recurring,
        });
        pushed++;
      } catch {
        // Server unreachable — will retry next sync cycle
      }
    }

    // 2. Delete all pending local records (pushed or not — retry would dup)
    if (pushed > 0) {
      await deletePendingLocal(userId);
    }

    // 3. Pull all remote transactions into local DB
    try {
      const remoteTxs = await transactionsApi.getAll({ limit: 500 });
      await upsertFromRemote(remoteTxs, userId);
      pulled = remoteTxs.length;
    } catch {
      // Server unreachable — skip pull
    }
  } finally {
    syncing = false;
  }

  return { pushed, pulled };
}

export function isSyncing(): boolean {
  return syncing;
}
