import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./hooks/useAuth";
import LoginPage from "./pages/LoginPage";
import DashboardPage from "./pages/DashboardPage";

const ProtectedRoute = ({ isAuthenticated, children }) => {
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  return children;
};

export default function App() {
  const { user, loading, isAuthenticated, login, logout } = useAuth();

  if (loading) {
    return (
      <main className="flex min-h-screen items-center justify-center" data-testid="app-loading-state">
        <p className="font-mono text-sm text-zinc-400" data-testid="app-loading-text">
          Bootstrapping operator session...
        </p>
      </main>
    );
  }

  return (
    <Routes>
      <Route
        path="/login"
        element={
          isAuthenticated ? (
            <Navigate to="/" replace />
          ) : (
            <LoginPage
              onLogin={async (username, password) => {
                await login(username, password);
              }}
            />
          )
        }
      />
      <Route
        path="/"
        element={
          <ProtectedRoute isAuthenticated={isAuthenticated}>
            <DashboardPage user={user} onLogout={logout} />
          </ProtectedRoute>
        }
      />
      <Route path="*" element={<Navigate to={isAuthenticated ? "/" : "/login"} replace />} />
    </Routes>
  );
}
