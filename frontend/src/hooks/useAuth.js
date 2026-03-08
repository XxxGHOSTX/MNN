import { useEffect, useMemo, useState } from "react";
import { clearSession, getAccessToken, getProfile, loginOperator } from "../services/api";

export const useAuth = () => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const bootstrap = async () => {
      const token = getAccessToken();
      if (!token) {
        setLoading(false);
        return;
      }
      try {
        const profile = await getProfile();
        setUser(profile);
      } catch {
        clearSession();
        setUser(null);
      } finally {
        setLoading(false);
      }
    };

    bootstrap();
  }, []);

  const login = async (username, password) => {
    await loginOperator(username, password);
    const profile = await getProfile();
    setUser(profile);
    return profile;
  };

  const logout = () => {
    clearSession();
    setUser(null);
  };

  return useMemo(
    () => ({
      user,
      loading,
      isAuthenticated: Boolean(user),
      login,
      logout,
    }),
    [user, loading]
  );
};
