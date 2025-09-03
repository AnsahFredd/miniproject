import React, {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
} from "react";
import { User, AuthContextType, SignupPayload } from "../types/customTypes";
import { analytics } from "../hooks/useAnalytics";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import toast from "react-hot-toast";

const API = import.meta.env.VITE_API_BASE_URL;
console.log("API base URL:", API);

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Safe JWT parsing
const parseJwt = (token: string) => {
  try {
    const base64 = token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/");
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split("")
        .map((c) => "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2))
        .join("")
    );
    return JSON.parse(jsonPayload);
  } catch (err) {
    return null;
  }
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(localStorage.getItem("token"));
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const navigate = useNavigate();

  const logout = useCallback(() => {
    setToken(null);
    setUser(null);
    setError(null);
    localStorage.removeItem("token");
    localStorage.removeItem("user_id");
    analytics.track("user_logout");
    navigate("/login");
  }, [navigate]);

  const hasRole = useCallback(
    (role: string): boolean => user?.roles?.includes(role) || false,
    [user]
  );

  const hasPermission = useCallback(
    (permission: string): boolean => user?.permission?.includes(permission) || false,
    [user]
  );

  const refreshToken = useCallback(async () => {
    try {
      const res = await axios.post(
        `${API}/auth/refresh`,
        null,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
          withCredentials: true,
        }
      );

      // Handle nested response structure
      const responseData = res.data.data || res.data;
      const accessToken = responseData.accessToken;

      if (!accessToken) throw new Error("No access token received");

      setToken(accessToken);
      localStorage.setItem("token", accessToken);
      setError(null);
      analytics.track("token_refreshed");

      return accessToken;
    } catch (error) {
      console.error("Token refresh error", error);
      setError("Session expired. Please log in again");
      logout();
    }
  }, [token, logout]);

  // Auto-refresh timer
  useEffect(() => {
    if (!token) return;

    const payload = parseJwt(token);
    if (!payload || !payload.exp) {
      console.error("Invalid token payload.");
      logout();
      return;
    }

    const expiryTime = payload.exp * 1000;
    const currentTime = Date.now();
    const timeUntilExpiry = expiryTime - currentTime;

    if (timeUntilExpiry > 0) {
      const refreshTime = Math.max(timeUntilExpiry - 5 * 60 * 1000, 60000);
      const refreshTimer = setTimeout(refreshToken, refreshTime);
      return () => clearTimeout(refreshTimer);
    } else {
      logout();
    }
  }, [token, refreshToken, logout]);

  const signup = async ({ email, password, name }: SignupPayload) => {
    try {
      setLoading(true);
      setError(null);

      const res = await axios.post(
        `${API}/auth/signup`,
        { email, password, name },
        {
          headers: { "Content-Type": "application/json" },
          withCredentials: true,
        }
      );

      // Handle nested response structure
      const responseData = res.data.data || res.data;
      const { message, email: userEmail, requires_confirmation } = responseData;

      analytics.track("user_signup", { email });

      if (requires_confirmation) {
        navigate(`/confirm-email?email=${encodeURIComponent(userEmail)}&status=pending`);
      }

      return { message, email: userEmail, requires_confirmation };
    } catch (error: any) {
      let errorMessage = "Signup failed";
      
      if (error.response?.data?.message) {
        errorMessage = error.response.data.message;
      } else if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      } else if (error.message) {
        errorMessage = error.message;
      }

      setError(errorMessage);
      analytics.track("signup_error", { error: errorMessage, email });
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const login = async (email: string, password: string) => {
    try {
      setLoading(true);
      setError(null);

      console.log("Attempting login with:", { email });

      const res = await axios.post(
        `${API}/auth/login`,
        { email, password },
        {
          headers: { "Content-Type": "application/json" },
          withCredentials: true,
        }
      );

      console.log("Login response:", res.data);

      // Handle nested response structure - backend returns { success: true, data: { accessToken, user }, message }
      const responseData = res.data.data || res.data;
      const { accessToken, user } = responseData;

      if (!accessToken || !user) {
        throw new Error("Invalid response from server - missing token or user data");
      }

      // Handle user ID mapping
      const processedUser = { ...user };
      if (processedUser._id && !processedUser.id) {
        processedUser.id = processedUser._id;
      }

      setToken(accessToken);
      setUser(processedUser);
      localStorage.setItem("token", accessToken);
      localStorage.setItem("user_id", processedUser.id);

      analytics.track("user_login", {
        userId: processedUser.id,
      });

      return { accessToken, user: processedUser };
    } catch (error: any) {
      let errorMessage = "Login failed";
      
      console.error("Login error:", error);

      if (error.response?.data?.message) {
        errorMessage = error.response.data.message;
      } else if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      } else if (error.message) {
        errorMessage = error.message;
      }

      setError(errorMessage);

      if (error?.response?.status === 429) {
        toast.error("Too many attempts. Please wait for few minutes and try again.")
      } 
      analytics.track("login_error", { error: errorMessage, email });
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const requestPasswordReset = async (email: string) => {
    try {
      setLoading(true);
      setError(null);
      await axios.post(`${API}/auth/forgot-password`, { email });
      analytics.track("password_reset_requested", { email });
    } catch (error: any) {
      const msg =
        error.response?.data?.message ||
        error.response?.data?.detail ||
        error.message ||
        "Failed to request password reset";
      setError(msg);
      analytics.track("forgot_password_error", { error: msg, email });
      throw new Error(msg);
    } finally {
      setLoading(false);
    }
  };

  const resetPassword = async (token: string, newPassword: string) => {
    try {
      setLoading(true);
      setError(null);
      await axios.post(`${API}/auth/password-reset`, {
        token,
        new_password: newPassword,
      });
      analytics.track("password_reset_success");
    } catch (error: any) {
      const msg =
        error.response?.data?.message ||
        error.response?.data?.detail ||
        error.message ||
        "Failed to reset password";
      setError(msg);
      analytics.track("reset_password_error", { error: msg });
      throw new Error(msg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const InitializeAuth = async () => {
      if (token) {
        try {
          const res = await axios.get(`${API}/auth/me`, {
            headers: {
              Authorization: `Bearer ${token}`,
            },
            withCredentials: true,
          });

          // Handle nested response structure
          let userData = res.data.data || res.data;
          
          // Handle user ID mapping
          if (userData._id && !userData.id) {
            userData.id = userData._id;
          }

          setUser(userData);
        } catch (error) {
          console.log("Auth initialization error", error);
          logout();
        }
      }
      setLoading(false);
    };

    InitializeAuth();
  }, [token, logout]);

  const value: AuthContextType = {
    token,
    user,
    loading,
    error,
    login,
    signup,
    logout,
    refreshToken,
    hasPermission,
    hasRole,
    requestPasswordReset,
    resetPassword,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};