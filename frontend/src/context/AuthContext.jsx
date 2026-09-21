import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  clearAccessToken,
  getAccessToken,
  getCurrentUser,
  loginRequest,
  setAccessToken,
} from "../services/api.js";


const AuthContext = createContext(null);


export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [isInitializing, setIsInitializing] =
    useState(true);


  const logout = useCallback(() => {
    clearAccessToken();
    setUser(null);
  }, []);


  const loadCurrentUser = useCallback(
    async () => {
      const token = getAccessToken();

      if (!token) {
        setUser(null);
        setIsInitializing(false);
        return;
      }

      try {
        const currentUser =
          await getCurrentUser();

        setUser(currentUser);
      } catch {
        clearAccessToken();
        setUser(null);
      } finally {
        setIsInitializing(false);
      }
    },
    []
  );


  useEffect(() => {
    loadCurrentUser();
  }, [loadCurrentUser]);


  useEffect(() => {
    const handleUnauthorized = () => {
      setUser(null);
    };

    window.addEventListener(
      "aegis:unauthorized",
      handleUnauthorized
    );

    return () => {
      window.removeEventListener(
        "aegis:unauthorized",
        handleUnauthorized
      );
    };
  }, []);


  const login = useCallback(
    async (username, password) => {
      const tokenResponse =
        await loginRequest(
          username,
          password
        );

      setAccessToken(
        tokenResponse.access_token
      );

      try {
        const currentUser =
          await getCurrentUser();

        setUser(currentUser);

        return currentUser;
      } catch (error) {
        clearAccessToken();
        setUser(null);
        throw error;
      }
    },
    []
  );


  const hasRole = useCallback(
    (...roles) => {
      if (!user) {
        return false;
      }

      return roles.includes(user.role);
    },
    [user]
  );


  const value = useMemo(
    () => ({
      user,
      isAuthenticated: Boolean(user),
      isInitializing,
      login,
      logout,
      hasRole,
    }),
    [
      user,
      isInitializing,
      login,
      logout,
      hasRole,
    ]
  );


  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}


export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error(
      "useAuth must be used inside AuthProvider."
    );
  }

  return context;
}