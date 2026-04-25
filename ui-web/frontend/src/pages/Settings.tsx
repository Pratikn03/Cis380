import { useEffect, useState } from "react";
import { ErrorState, JsonBlock, PageShell, Panel, PrimaryButton, TextInput } from "../components/DashboardPrimitives";
import { useAuth } from "../context/AuthContext";
import { passwordResetConfirm, passwordResetRequest, totpEnroll, totpVerify, updateUserSettings, userSettings } from "../services/endpoints";

export default function Settings() {
  const { viewer } = useAuth();
  const [settings, setSettings] = useState({ theme: "system", default_model: "auto", agent_token_cap: 2048 });
  const [totp, setTotp] = useState<Record<string, any> | null>(null);
  const [totpCode, setTotpCode] = useState("");
  const [resetToken, setResetToken] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    userSettings()
      .then((response) => setSettings(response.data.settings))
      .catch((err) => setError(err.response?.data?.detail || err.message));
  }, []);

  const save = async () => {
    const { data } = await updateUserSettings(settings);
    setSettings(data.settings);
    setStatus("Settings saved.");
  };

  const enroll = async () => {
    const { data } = await totpEnroll();
    setTotp(data);
  };

  const verify = async () => {
    await totpVerify({ code: totpCode });
    setStatus("TOTP enabled.");
  };

  const requestReset = async () => {
    const { data } = await passwordResetRequest({ username: viewer?.username });
    setStatus(data.reset_token ? `Reset token: ${data.reset_token}` : "Password reset requested.");
  };

  const confirmReset = async () => {
    await passwordResetConfirm({ token: resetToken, new_password: newPassword });
    setStatus("Password updated.");
  };

  return (
    <PageShell title="Settings" eyebrow="Per-user Preferences">
      <ErrorState message={error || status} />
      <div className="grid gap-4 lg:grid-cols-3">
        <Panel title="Preferences">
          <label className="text-sm text-fog">Theme</label>
          <TextInput value={settings.theme} onChange={(event) => setSettings((prev) => ({ ...prev, theme: event.target.value }))} />
          <label className="mt-3 block text-sm text-fog">Default model</label>
          <TextInput value={settings.default_model} onChange={(event) => setSettings((prev) => ({ ...prev, default_model: event.target.value }))} />
          <label className="mt-3 block text-sm text-fog">Agent token cap</label>
          <TextInput type="number" value={settings.agent_token_cap} onChange={(event) => setSettings((prev) => ({ ...prev, agent_token_cap: Number(event.target.value) }))} />
          <PrimaryButton onClick={save} className="mt-3">Save</PrimaryButton>
        </Panel>
        <Panel title="TOTP Enrollment">
          <PrimaryButton onClick={enroll}>Start Enrollment</PrimaryButton>
          {totp && <JsonBlock value={totp} />}
          <TextInput placeholder="6-digit code" value={totpCode} onChange={(event) => setTotpCode(event.target.value)} className="mt-3" />
          <PrimaryButton onClick={verify} disabled={!totpCode} className="mt-3">Verify TOTP</PrimaryButton>
        </Panel>
        <Panel title="Password Reset">
          <PrimaryButton onClick={requestReset}>Request Reset</PrimaryButton>
          <TextInput placeholder="reset token" value={resetToken} onChange={(event) => setResetToken(event.target.value)} className="mt-3" />
          <TextInput placeholder="new password" type="password" value={newPassword} onChange={(event) => setNewPassword(event.target.value)} className="mt-3" />
          <PrimaryButton onClick={confirmReset} disabled={!resetToken || !newPassword} className="mt-3">Confirm Reset</PrimaryButton>
        </Panel>
      </div>
    </PageShell>
  );
}
