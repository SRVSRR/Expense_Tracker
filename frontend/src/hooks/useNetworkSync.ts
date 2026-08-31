import { useEffect, useRef } from 'react';
import NetInfo, { NetInfoState } from '@react-native-community/netinfo';
import { useTransactionStore } from '../store/transactionStore';
import { useAuthStore } from '../store/authStore';

export function useNetworkSync() {
  const prevOnline = useRef<boolean>(true);
  const setIsOnline = useTransactionStore((s) => s.setIsOnline);
  const sync = useTransactionStore((s) => s.sync);
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);

  useEffect(() => {
    const unsubscribe = NetInfo.addEventListener((state: NetInfoState) => {
      const online = state.isConnected ?? false;
      setIsOnline(online);

      // Trigger sync when coming back online
      if (online && !prevOnline.current && isAuthenticated) {
        sync().catch(() => {});
      }

      prevOnline.current = online;
    });

    return () => unsubscribe();
  }, [isAuthenticated]);
}
