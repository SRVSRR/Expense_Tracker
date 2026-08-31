import * as SQLite from 'expo-sqlite';

let db: SQLite.SQLiteDatabase | null = null;

export async function getDatabase(): Promise<SQLite.SQLiteDatabase> {
  if (db) return db;
  db = await SQLite.openDatabaseAsync('expense_tracker.db');
  await db.execAsync(`
    CREATE TABLE IF NOT EXISTS local_transactions (
      id TEXT PRIMARY KEY,
      user_id TEXT NOT NULL,
      account_id TEXT NOT NULL,
      type TEXT NOT NULL,
      amount REAL NOT NULL,
      category TEXT NOT NULL,
      description TEXT NOT NULL,
      merchant TEXT,
      date TEXT NOT NULL,
      is_recurring INTEGER DEFAULT 0,
      created_at TEXT NOT NULL,
      updated_at TEXT NOT NULL,
      sync_status TEXT DEFAULT 'pending'
    );
    CREATE INDEX IF NOT EXISTS idx_lt_user ON local_transactions(user_id);
    CREATE INDEX IF NOT EXISTS idx_lt_sync ON local_transactions(sync_status);
    CREATE INDEX IF NOT EXISTS idx_lt_date ON local_transactions(date);
  `);
  return db;
}

export interface LocalTransaction {
  id: string;
  user_id: string;
  account_id: string;
  type: 'income' | 'expense';
  amount: number;
  category: string;
  description: string;
  merchant?: string;
  date: string;
  is_recurring: number;
  created_at: string;
  updated_at: string;
  sync_status: 'pending' | 'synced';
}

export async function insertLocal(tx: LocalTransaction): Promise<void> {
  const db = await getDatabase();
  await db.runAsync(
    `INSERT OR REPLACE INTO local_transactions
     (id, user_id, account_id, type, amount, category, description, merchant, date, is_recurring, created_at, updated_at, sync_status)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
    tx.id, tx.user_id, tx.account_id, tx.type, tx.amount, tx.category,
    tx.description, tx.merchant || null, tx.date, tx.is_recurring,
    tx.created_at, tx.updated_at, tx.sync_status
  );
}

export async function getLocalTransactions(
  userId: string,
  filters?: { type?: string; limit?: number; offset?: number }
): Promise<LocalTransaction[]> {
  const db = await getDatabase();
  let query = 'SELECT * FROM local_transactions WHERE user_id = ?';
  const params: any[] = [userId];

  if (filters?.type) {
    query += ' AND type = ?';
    params.push(filters.type);
  }

  query += ' ORDER BY date DESC, created_at DESC';

  if (filters?.limit) {
    query += ' LIMIT ?';
    params.push(filters.limit);
  }
  if (filters?.offset) {
    query += ' OFFSET ?';
    params.push(filters.offset);
  }

  return await db.getAllAsync<LocalTransaction>(query, ...params);
}

export async function getPendingLocal(userId: string): Promise<LocalTransaction[]> {
  const db = await getDatabase();
  return await db.getAllAsync<LocalTransaction>(
    'SELECT * FROM local_transactions WHERE user_id = ? AND sync_status = ?',
    userId, 'pending'
  );
}

export async function deleteLocal(id: string): Promise<void> {
  const db = await getDatabase();
  await db.runAsync('DELETE FROM local_transactions WHERE id = ?', id);
}

export async function deletePendingLocal(userId: string): Promise<void> {
  const db = await getDatabase();
  await db.runAsync(
    'DELETE FROM local_transactions WHERE user_id = ? AND sync_status = ?',
    userId, 'pending'
  );
}

export async function clearAllLocal(userId: string): Promise<void> {
  const db = await getDatabase();
  await db.runAsync('DELETE FROM local_transactions WHERE user_id = ?', userId);
}

export async function upsertFromRemote(transactions: any[], userId: string): Promise<void> {
  const db = await getDatabase();
  for (const tx of transactions) {
    await db.runAsync(
      `INSERT OR REPLACE INTO local_transactions
       (id, user_id, account_id, type, amount, category, description, merchant, date, is_recurring, created_at, updated_at, sync_status)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
      tx.id, userId, tx.account_id, tx.type, tx.amount, tx.category,
      tx.description, tx.merchant || null, tx.date, tx.is_recurring || 0,
      tx.created_at, tx.updated_at, 'synced'
    );
  }
}
