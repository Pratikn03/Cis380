import { useEffect, useState } from "react";
import { ErrorState, JsonBlock, PageShell, Panel, PrimaryButton, StatusPill, TextInput } from "../components/DashboardPrimitives";
import { useAuth } from "../context/AuthContext";
import { api } from "../services/api";
import { adminModelRegistry, auditLogs, featureFlags, updateFeatureFlags } from "../services/endpoints";

export default function Admin() {
  const { viewer } = useAuth();
  const [registry, setRegistry] = useState<Record<string, any> | null>(null);
  const [flags, setFlags] = useState<Record<string, boolean>>({});
  const [logs, setLogs] = useState<any[]>([]);
  const [users, setUsers] = useState<any[]>([]);
  const [roles, setRoles] = useState<any[]>([]);
  const [newUser, setNewUser] = useState({ username: "", password: "", roles: "viewer" });
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setError(null);
    try {
      const [reg, flagResponse, audit, userResponse, roleResponse] = await Promise.all([
        adminModelRegistry(),
        featureFlags(),
        auditLogs({ limit: 50 }),
        api.get("/api/v1/admin/users"),
        api.get("/api/v1/admin/roles"),
      ]);
      setRegistry(reg.data);
      setFlags(flagResponse.data.flags || {});
      setLogs(audit.data.logs || []);
      setUsers(userResponse.data || []);
      setRoles(roleResponse.data || []);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const saveFlags = async () => {
    await updateFeatureFlags(flags);
    await load();
  };

  const createUser = async () => {
    await api.post("/api/v1/admin/users", {
      username: newUser.username,
      password: newUser.password,
      roles: newUser.roles.split(",").map((role) => role.trim()).filter(Boolean),
    });
    setNewUser({ username: "", password: "", roles: "viewer" });
    await load();
  };

  return (
    <PageShell title="Admin" eyebrow={`Signed in as ${viewer?.username || "unknown"}`}>
      <ErrorState message={error} />
      <div className="grid gap-4 xl:grid-cols-2">
        <Panel title="Model Registry">
          <div className="grid gap-2 md:grid-cols-2">
            {(registry?.models || []).map((model: any) => (
              <article key={model.domain} className="rounded-md border border-line bg-white p-3">
                <div className="flex items-center justify-between gap-2">
                  <strong>{model.domain}</strong>
                  <StatusPill status={model.thresholdResult} />
                </div>
                <p className="mt-1 truncate text-xs text-fog">{model.path}</p>
                <p className="mt-1 text-xs text-fog">Smoke: {model.smokeInference}</p>
              </article>
            ))}
          </div>
        </Panel>
        <Panel title="Feature Flags">
          <div className="space-y-2">
            {Object.entries(flags).map(([key, value]) => (
              <label key={key} className="flex items-center justify-between rounded-md border border-line bg-white p-2 text-sm">
                <span>{key}</span>
                <input
                  type="checkbox"
                  checked={value}
                  onChange={(event) => setFlags((prev) => ({ ...prev, [key]: event.target.checked }))}
                />
              </label>
            ))}
          </div>
          <PrimaryButton onClick={saveFlags} className="mt-3">
            Save Flags
          </PrimaryButton>
        </Panel>
        <Panel title="Users + Roles">
          <div className="mb-3 grid gap-2 md:grid-cols-3">
            <TextInput placeholder="username" value={newUser.username} onChange={(event) => setNewUser((prev) => ({ ...prev, username: event.target.value }))} />
            <TextInput placeholder="password" type="password" value={newUser.password} onChange={(event) => setNewUser((prev) => ({ ...prev, password: event.target.value }))} />
            <TextInput placeholder="roles" value={newUser.roles} onChange={(event) => setNewUser((prev) => ({ ...prev, roles: event.target.value }))} />
          </div>
          <PrimaryButton onClick={createUser} disabled={!newUser.username || !newUser.password}>
            Create User
          </PrimaryButton>
          <JsonBlock value={{ users, roles }} />
        </Panel>
        <Panel title="Audit Logs">
          <JsonBlock value={logs} />
        </Panel>
      </div>
    </PageShell>
  );
}
