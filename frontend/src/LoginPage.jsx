import { useState } from "react";
import { Boxes, LockKeyhole } from "lucide-react";

export default function LoginPage({ onLogin }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event) {
    event.preventDefault();
    setError("");
    setBusy(true);
    try {
      await onLogin({ username, password });
    } catch (err) {
      setError(err.response?.data?.detail || "Não foi possível entrar. Verifique a conexão com a API.");
    } finally {
      setBusy(false);
    }
  }

  return <main className="auth-screen">
    <form className="panel auth-panel" onSubmit={submit}>
      <div className="auth-brand"><div className="brand-icon"><Boxes size={24} /></div><div><h1>StockFlow</h1><p>Acesso à loja</p></div></div>
      <label className="field"><span>Usuário</span><input autoComplete="username" required value={username} onChange={event => setUsername(event.target.value)} /></label>
      <label className="field"><span>Senha</span><input type="password" autoComplete="current-password" required value={password} onChange={event => setPassword(event.target.value)} /></label>
      {error && <div className="error-banner">{error}</div>}
      <button className="primary-button submit-button" disabled={busy}><LockKeyhole size={17} /> {busy ? "Entrando..." : "Entrar"}</button>
    </form>
  </main>;
}
