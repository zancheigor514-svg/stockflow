import { useState } from "react";
import axios from "./api.js";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function SecurityPage({ onPasswordChanged }) {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event) {
    event.preventDefault();
    if (newPassword.length < 14) return alert("Use uma senha com pelo menos 14 caracteres.");
    if (newPassword !== confirmation) return alert("A confirmação da senha não confere.");
    setBusy(true);
    try {
      await axios.post(`${API}/auth/password`, { current_password: currentPassword, new_password: newPassword });
      alert("Senha alterada. Entre novamente com a nova senha.");
      onPasswordChanged();
    } catch (err) {
      alert(err.response?.data?.detail || "Não foi possível alterar a senha.");
    } finally {
      setBusy(false);
    }
  }

  return <section className="panel security-panel">
    <div className="panel-heading"><div><h3>Segurança da conta</h3><p>Troque a senha usada para acessar o StockFlow.</p></div></div>
    <form onSubmit={submit}>
      <label className="field"><span>Senha atual</span><input required type="password" autoComplete="current-password" value={currentPassword} onChange={event => setCurrentPassword(event.target.value)} /></label>
      <label className="field"><span>Nova senha (mínimo 14 caracteres)</span><input required minLength="14" type="password" autoComplete="new-password" value={newPassword} onChange={event => setNewPassword(event.target.value)} /></label>
      <label className="field"><span>Confirme a nova senha</span><input required minLength="14" type="password" autoComplete="new-password" value={confirmation} onChange={event => setConfirmation(event.target.value)} /></label>
      <button className="primary-button" disabled={busy}>{busy ? "Salvando..." : "Alterar senha"}</button>
    </form>
  </section>;
}
