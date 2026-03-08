import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import {
  Activity,
  Database,
  LogOut,
  Send,
  ShieldCheck,
  TerminalSquare,
  Timer,
  Wifi,
} from "lucide-react";
import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Card } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { runQuery, getDashboardOverview, getBackendUrl } from "../services/api";

const getBadgeVariant = (status, mode) => {
  if (mode === "mock") return "mock";
  if (status === "healthy") return "healthy";
  if (status === "degraded") return "degraded";
  return "down";
};

const feedbackToChart = (feedback) => {
  const ratings = feedback?.rating_distribution || {};
  return [1, 2, 3, 4, 5].map((rating) => ({
    rating: `${rating}★`,
    count: ratings[rating] ?? ratings[String(rating)] ?? 0,
  }));
};

export default function DashboardPage({ user, onLogout }) {
  const [overview, setOverview] = useState(null);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("deterministic inference");
  const [queryResponse, setQueryResponse] = useState(null);
  const [runningQuery, setRunningQuery] = useState(false);

  const refreshOverview = async () => {
    try {
      setLoading(true);
      const data = await getDashboardOverview();
      setOverview(data);
    } catch (error) {
      toast.error(error.message || "Unable to load dashboard data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshOverview();
  }, []);

  const runOperatorQuery = async () => {
    if (!query.trim()) {
      toast.error("Please enter a query first.");
      return;
    }

    try {
      setRunningQuery(true);
      const response = await runQuery(query);
      setQueryResponse(response);
      toast.success("Query completed successfully.");
      await refreshOverview();
    } catch (error) {
      toast.error(error.message || "Query execution failed.");
    } finally {
      setRunningQuery(false);
    }
  };

  const chartData = useMemo(() => feedbackToChart(overview?.feedback), [overview]);
  const metrics = overview?.metrics;

  return (
    <main className="mx-auto w-full max-w-[1440px] p-6 md:p-8" data-testid="dashboard-root">
      <header
        className="mb-6 flex flex-wrap items-center justify-between gap-4 border-b border-white/10 pb-4"
        data-testid="dashboard-header"
      >
        <div>
          <h1 className="text-4xl md:text-5xl tracking-tight" data-testid="dashboard-title">
            MNN OPS
          </h1>
          <p className="mt-2 text-sm text-zinc-400" data-testid="dashboard-subtitle">
            Operator: {user?.username} · Backend: <span className="font-mono">{getBackendUrl()}</span>
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <Badge variant="healthy" data-testid="dashboard-connection-status-badge">
            <Wifi className="mr-1 h-3.5 w-3.5" /> Connected
          </Badge>
          <Button data-testid="dashboard-refresh-button" variant="outline" onClick={refreshOverview}>
            Refresh
          </Button>
          <Button data-testid="dashboard-logout-button" variant="danger" onClick={onLogout}>
            <LogOut className="mr-2 h-4 w-4" /> Logout
          </Button>
        </div>
      </header>

      <section className="grid grid-cols-1 gap-4 md:grid-cols-3 md:gap-6" data-testid="dashboard-metrics-row">
        <Card data-testid="metric-total-requests-card">
          <p className="text-xs uppercase tracking-wide text-zinc-500">Total Requests</p>
          <p className="mt-2 text-3xl font-black" data-testid="metric-total-requests-value">
            {loading ? "..." : metrics?.total_queries ?? 0}
          </p>
        </Card>
        <Card data-testid="metric-avg-latency-card">
          <p className="text-xs uppercase tracking-wide text-zinc-500">Avg Latency</p>
          <p className="mt-2 text-3xl font-black" data-testid="metric-avg-latency-value">
            {loading ? "..." : metrics?.avg_latency_seconds ?? 0}s
          </p>
        </Card>
        <Card data-testid="metric-total-errors-card">
          <p className="text-xs uppercase tracking-wide text-zinc-500">Total Errors</p>
          <p className="mt-2 text-3xl font-black text-red-400" data-testid="metric-total-errors-value">
            {loading ? "..." : metrics?.total_errors ?? 0}
          </p>
        </Card>
      </section>

      <section className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-12 md:gap-6" data-testid="dashboard-main-grid">
        <Card className="md:col-span-8" data-testid="query-runner-card">
          <div className="flex items-center justify-between gap-2">
            <h2 className="text-2xl md:text-3xl tracking-tight" data-testid="query-runner-title">
              Query Runner
            </h2>
            <TerminalSquare className="h-5 w-5 text-[#007AFF]" />
          </div>

          <textarea
            data-testid="query-runner-input"
            className="mt-4 min-h-28 w-full rounded-sm border border-white/15 bg-black/35 p-3 font-mono text-sm text-white outline-none transition-colors duration-200 focus:border-[#007AFF]"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />

          <div className="mt-3 flex justify-end">
            <Button
              data-testid="query-runner-submit-button"
              onClick={runOperatorQuery}
              disabled={runningQuery}
            >
              <Send className="mr-2 h-4 w-4" />
              {runningQuery ? "Running..." : "Run Query"}
            </Button>
          </div>

          <pre
            data-testid="query-runner-output"
            className="mt-4 max-h-72 overflow-auto rounded-sm border border-white/10 bg-black/50 p-4 text-xs text-zinc-200"
          >
            {queryResponse ? JSON.stringify(queryResponse, null, 2) : "Run a query to see deterministic output."}
          </pre>
        </Card>

        <Card className="md:col-span-4" data-testid="system-status-card">
          <div className="flex items-center justify-between gap-2">
            <h2 className="text-2xl tracking-tight" data-testid="system-status-title">
              System Status
            </h2>
            <Database className="h-5 w-5 text-[#007AFF]" />
          </div>
          <div className="mt-4 space-y-3" data-testid="system-status-list">
            {(overview?.infra || []).map((service) => (
              <div
                key={service.name}
                className="rounded-sm border border-white/10 bg-black/25 p-3"
                data-testid={`system-status-item-${service.name}`}
              >
                <div className="flex items-center justify-between gap-2">
                  <p className="font-semibold uppercase tracking-wide text-zinc-200">{service.name}</p>
                  <Badge
                    variant={getBadgeVariant(service.status, service.mode)}
                    data-testid={`system-status-badge-${service.name}`}
                  >
                    {service.mode === "mock" ? "MOCK" : service.status}
                  </Badge>
                </div>
                <p className="mt-2 text-xs text-zinc-500" data-testid={`system-status-detail-${service.name}`}>
                  {service.detail}
                </p>
              </div>
            ))}
          </div>
        </Card>

        <Card className="md:col-span-6" data-testid="feedback-stats-card">
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-5 w-5 text-[#007AFF]" />
            <h2 className="text-2xl tracking-tight" data-testid="feedback-stats-title">
              Feedback Distribution
            </h2>
          </div>
          <div className="mt-4 h-64" data-testid="feedback-stats-chart">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData}>
                <XAxis dataKey="rating" stroke="#A1A1AA" />
                <YAxis stroke="#A1A1AA" allowDecimals={false} />
                <Tooltip />
                <Bar dataKey="count" fill="#007AFF" radius={[2, 2, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card className="md:col-span-6" data-testid="cache-summary-card">
          <div className="flex items-center gap-2">
            <Activity className="h-5 w-5 text-[#007AFF]" />
            <h2 className="text-2xl tracking-tight" data-testid="cache-summary-title">
              Cache and Throughput
            </h2>
          </div>
          <ul className="mt-4 space-y-3 text-sm text-zinc-300" data-testid="cache-summary-list">
            <li className="flex items-center justify-between">
              <span className="inline-flex items-center gap-2">
                <Timer className="h-4 w-4" /> Cache Hits
              </span>
              <strong data-testid="cache-hits-value">{metrics?.cache?.hits ?? 0}</strong>
            </li>
            <li className="flex items-center justify-between">
              <span className="inline-flex items-center gap-2">
                <Timer className="h-4 w-4" /> Cache Misses
              </span>
              <strong data-testid="cache-misses-value">{metrics?.cache?.misses ?? 0}</strong>
            </li>
            <li className="flex items-center justify-between">
              <span className="inline-flex items-center gap-2">
                <Timer className="h-4 w-4" /> Cache Size
              </span>
              <strong data-testid="cache-size-value">{metrics?.cache?.size ?? 0}</strong>
            </li>
          </ul>
        </Card>
      </section>
    </main>
  );
}
