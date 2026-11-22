import { useEffect, useState } from "react";
import axios from "axios";
import { Search, Plus, Pencil, FileText, CreditCard, Check } from "lucide-react";

const API = "http://localhost:8000";
const paymentMethods = ["Dinheiro", "Pix", "Cartão de crédito", "Cartão de débito", "Transferência", "Outros"];

function Field({ label, required, children }) {
  return <label className="field"><span>{label}{required ? " *" : ""}</span>{children}</label>;
}

function formatCpf(value) {
  const digits = String(value || "").replace(/\D/g, "").slice(0, 11);
  if (digits.length <= 3) return digits;
  if (digits.length <= 6) return `${digits.slice(0, 3)}.${digits.slice(3)}`;
  if (digits.length <= 9) return `${digits.slice(0, 3)}.${digits.slice(3, 6)}.${digits.slice(6)}`;
  return `${digits.slice(0, 3)}.${digits.slice(3, 6)}.${digits.slice(6, 9)}-${digits.slice(9)}`;
}

export default function CreditPage({ money, onDataChanged }) {
  const [customers, setCustomers] = useState([]);
  const [search, setSearch] = useState("");
  const [selectedId, setSelectedId] = useState(null);
  const [account, setAccount] = useState(null);
  const [formOpen, setFormOpen] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [saving, setSaving] = useState(false);
  const [loadingAccount, setLoadingAccount] = useState(false);
  const [selectedInstallments, setSelectedInstallments] = useState([]);
  const [paymentMethod, setPaymentMethod] = useState("Pix");
  const [form, setForm] = useState({ cpf: "", rg: "", full_name: "", address: "", observations: "" });
  const [files, setFiles] = useState({ document_photo: null, person_photo: null, residence_proof: null });

  async function loadCustomers(term = search) {
    try {
      const { data } = await axios.get(`${API}/credit/customers`, { params: { q: term } });
      setCustomers(Array.isArray(data) ? data : []);
    } catch (err) {
      alert(err.response?.data?.detail || "Não foi possível carregar os clientes do crediário.");
    }
  }

  async function loadAccount(customerId) {
    if (!customerId) return;
    setLoadingAccount(true);
    try {
      const { data } = await axios.get(`${API}/credit/customers/${customerId}/account`);
      setAccount(data);
      setSelectedId(customerId);
      setSelectedInstallments([]);
    } catch (err) {
      alert(err.response?.data?.detail || "Não foi possível carregar a conta do cliente.");
    } finally {
      setLoadingAccount(false);
    }
  }

  useEffect(() => {
    loadCustomers("");
  }, []);

  function startCreate() {
    setEditingId(null);
    setForm({ cpf: "", rg: "", full_name: "", address: "", observations: "" });
    setFiles({ document_photo: null, person_photo: null, residence_proof: null });
    setFormOpen(true);
  }

  function startEdit() {
    const customer = account?.customer;
    if (!customer) return;
    setEditingId(customer.id);
    setForm({
      cpf: formatCpf(customer.cpf),
      rg: customer.rg,
      full_name: customer.full_name,
      address: customer.address,
      observations: customer.observations || ""
    });
    setFiles({ document_photo: null, person_photo: null, residence_proof: null });
    setFormOpen(true);
  }

  async function saveCustomer(e) {
    e.preventDefault();
    if (!editingId && (!files.document_photo || !files.person_photo || !files.residence_proof)) {
      alert("Envie a foto do documento, da pessoa e do comprovante de residência.");
      return;
    }
    const data = new FormData();
    Object.entries(form).forEach(([key, value]) => data.append(key, value));
    Object.entries(files).forEach(([key, value]) => { if (value) data.append(key, value); });
    setSaving(true);
    try {
      const response = editingId
        ? await axios.put(`${API}/credit/customers/${editingId}`, data)
        : await axios.post(`${API}/credit/customers`, data);
      setFormOpen(false);
      setFiles({ document_photo: null, person_photo: null, residence_proof: null });
      await loadCustomers("");
      await loadAccount(response.data.id);
    } catch (err) {
      alert(err.response?.data?.detail || "Não foi possível salvar o cliente.");
    } finally {
      setSaving(false);
    }
  }

  function toggleInstallment(id) {
    setSelectedInstallments(current => current.includes(id)
      ? current.filter(value => value !== id)
      : [...current, id]
    );
  }

  const allInstallments = (account?.contracts || []).flatMap(contract =>
    contract.installments.map(installment => ({ ...installment, contract }))
  );
  const dueNowEstimate = allInstallments
    .filter(installment => selectedInstallments.includes(installment.id))
    .reduce((sum, installment) => sum + Number(installment.total_due || 0), 0);

  async function collectSelected() {
    if (!selectedId || selectedInstallments.length === 0) return;
    try {
      const { data } = await axios.post(`${API}/credit/payments`, {
        customer_id: selectedId,
        installment_ids: selectedInstallments,
        payment_method: paymentMethod
      });
      alert(`Pagamento registrado: ${money(data.amount)} (${money(data.interest_amount)} de juros). Recibo #${data.receipt_id}.`);
      setSelectedInstallments([]);
      await loadAccount(selectedId);
      await loadCustomers("");
      await onDataChanged?.();
    } catch (err) {
      alert(err.response?.data?.detail || "Não foi possível registrar o pagamento.");
    }
  }

  return (
    <div className="credit-layout">
      <section className="panel credit-customer-list">
        <div className="panel-heading">
          <div><h3>Clientes do crediário</h3><p>Busque pelo nome ou CPF, ou cadastre uma pessoa.</p></div>
          <button type="button" className="primary-button" onClick={startCreate}><Plus size={16} /> Novo cliente</button>
        </div>
        <form className="search-box" onSubmit={e => { e.preventDefault(); loadCustomers(search); }}>
          <Search size={18} /><input placeholder="Buscar nome ou CPF..." value={search} onChange={e => setSearch(e.target.value)} />
        </form>
        <div className="credit-customer-results">
          {customers.map(customer => (
            <button type="button" key={customer.id} className={`credit-customer-row ${selectedId === customer.id ? "selected" : ""}`} onClick={() => { setFormOpen(false); loadAccount(customer.id); }}>
              <span><strong>{customer.full_name}</strong><small>CPF {formatCpf(customer.cpf)}</small></span>
              <b>#{customer.id}</b>
            </button>
          ))}
          {customers.length === 0 && <div className="empty-state">Nenhum cliente encontrado.</div>}
        </div>
      </section>

      <div className="credit-account-column">
        {formOpen && (
          <section className="panel">
            <div className="panel-heading"><div><h3>{editingId ? "Editar cliente" : "Novo cliente"}</h3><p>Fotos dos documentos são opcionais. Cada arquivo pode ter até 5 MB.</p></div></div>
            <form onSubmit={saveCustomer}>
              <div className="credit-form-grid">
                <Field label="CPF" required><input required inputMode="numeric" maxLength="14" value={form.cpf} onChange={e => setForm({ ...form, cpf: formatCpf(e.target.value) })} /></Field>
                <Field label="RG" required><input required maxLength="30" value={form.rg} onChange={e => setForm({ ...form, rg: e.target.value })} /></Field>
              </div>
              <Field label="Nome completo" required><input required maxLength="150" value={form.full_name} onChange={e => setForm({ ...form, full_name: e.target.value })} /></Field>
              <Field label="Endereço" required><textarea required maxLength="500" value={form.address} onChange={e => setForm({ ...form, address: e.target.value })} /></Field>
              <div className="credit-form-grid">
                <Field label="Foto do documento"><input type="file" accept="image/png,image/jpeg,image/webp" onChange={e => setFiles({ ...files, document_photo: e.target.files?.[0] || null })} /></Field>
                <Field label="Foto da pessoa"><input type="file" accept="image/png,image/jpeg,image/webp" onChange={e => setFiles({ ...files, person_photo: e.target.files?.[0] || null })} /></Field>
                <Field label="Comprovante de residência"><input type="file" accept="image/png,image/jpeg,image/webp" onChange={e => setFiles({ ...files, residence_proof: e.target.files?.[0] || null })} /></Field>
              </div>
              <Field label="Observações"><textarea maxLength="2000" value={form.observations} onChange={e => setForm({ ...form, observations: e.target.value })} /></Field>
              <div className="credit-form-actions">
                <button type="button" className="text-button" onClick={() => setFormOpen(false)}>Cancelar</button>
                <button type="submit" className="primary-button" disabled={saving}><Check size={16} /> {saving ? "Salvando..." : "Salvar cliente"}</button>
              </div>
            </form>
          </section>
        )}

        {!formOpen && loadingAccount && <div className="panel loading">Carregando conta do cliente...</div>}
        {!formOpen && !loadingAccount && account && (
          <>
            <section className="panel">
              <div className="panel-heading">
                <div><h3>{account.customer.full_name}</h3><p>Cliente #{account.customer.id} · CPF {formatCpf(account.customer.cpf)} · RG {account.customer.rg}</p></div>
                <button type="button" className="text-button" onClick={startEdit}><Pencil size={15} /> Editar cadastro</button>
              </div>
              <p className="credit-customer-address">{account.customer.address}</p>
              {account.customer.observations && <p className="credit-observations">{account.customer.observations}</p>}
              <div className="credit-document-links">
                {[["identity", "Documento", account.customer.has_document_photo], ["person", "Foto da pessoa", account.customer.has_person_photo], ["residence", "Comprovante", account.customer.has_residence_proof]].filter(([, , exists]) => exists).map(([kind, label]) => (
                  <a key={kind} href={`${API}/credit/customers/${account.customer.id}/documents/${kind}`} target="_blank" rel="noreferrer"><FileText size={15} /> {label}</a>
                ))}
              </div>
            </section>

            <section className="panel">
              <div className="panel-heading"><div><h3>Parcelas e pagamentos</h3><p>Marque uma ou mais parcelas em aberto para quitar.</p></div><CreditCard size={20} /></div>
              {account.contracts.length === 0 ? <div className="empty-state">Este cliente ainda não tem contratos de crediário.</div> : account.contracts.map(contract => (
                <div className="credit-contract" key={contract.id}>
                  <div className="credit-contract-title"><strong>Contrato #{contract.id} · Venda #{contract.sale_id}</strong><span>{contract.installment_count}x de {money(contract.total_amount / contract.installment_count)} · {contract.status === "quitado" ? "Quitado" : "Em aberto"}</span></div>
                  <div className="table-wrap"><table className="credit-installment-table"><thead><tr><th></th><th>Parcela</th><th>Vencimento</th><th>Pagamento</th><th>Principal</th><th>Juros</th><th>Total</th><th>Status</th></tr></thead><tbody>
                    {contract.installments.map(installment => {
                      const canSelect = installment.status === "pendente";
                      return <tr key={installment.id}>
                        <td>{canSelect && <input aria-label={`Selecionar parcela ${installment.installment_number}`} type="checkbox" checked={selectedInstallments.includes(installment.id)} onChange={() => toggleInstallment(installment.id)} />}</td>
                        <td>{installment.installment_number}/{contract.installment_count}</td>
                        <td>{new Date(`${installment.due_date}T12:00:00`).toLocaleDateString("pt-BR")}</td>
                        <td>{installment.paid_at ? new Date(installment.paid_at).toLocaleString("pt-BR") : "—"}</td>
                        <td>{money(installment.amount)}</td>
                        <td>{money(canSelect ? installment.interest_due : installment.interest_paid)}</td>
                        <td>{money(canSelect ? installment.total_due : Number(installment.amount) + Number(installment.interest_paid || 0))}</td>
                        <td><span className={`tag ${canSelect ? (installment.display_status === "atrasada" ? "tag-red" : "tag-yellow") : "tag-green"}`}>{installment.display_status}</span>{canSelect && installment.days_late > 0 && <small className="credit-late-days">{installment.days_late} dias</small>}</td>
                      </tr>;
                    })}
                  </tbody></table></div>
                </div>
              ))}
              {selectedInstallments.length > 0 && <div className="credit-payment-bar">
                <div><strong>{selectedInstallments.length} parcela(s) selecionada(s)</strong><span>Estimativa com juros de hoje: {money(dueNowEstimate)}</span></div>
                <Field label="Recebido em"><select value={paymentMethod} onChange={e => setPaymentMethod(e.target.value)}>{paymentMethods.map(method => <option key={method}>{method}</option>)}</select></Field>
                <button type="button" className="primary-button" onClick={collectSelected}><Check size={16} /> Registrar pagamento</button>
              </div>}
            </section>

            <section className="panel">
              <div className="panel-heading"><div><h3>Histórico de recebimentos</h3><p>Pagamentos registrados para este cliente.</p></div></div>
              {account.receipts.length === 0 ? <div className="empty-state">Nenhum recebimento registrado.</div> : <div className="table-wrap"><table><thead><tr><th>Recibo</th><th>Data do pagamento</th><th>Detalhe</th><th>Forma</th><th>Juros</th><th>Recebido</th></tr></thead><tbody>{account.receipts.map(receipt => <tr key={receipt.id}><td>#{receipt.id}</td><td>{new Date(receipt.paid_at).toLocaleString("pt-BR")}</td><td>{receipt.installments_paid ? `${receipt.installments_paid} parcela(s)` : "Entrada da venda"}</td><td>{receipt.payment_method}</td><td>{money(receipt.interest_amount)}</td><td><strong>{money(receipt.amount)}</strong></td></tr>)}</tbody></table></div>}
            </section>
          </>
        )}
        {!formOpen && !loadingAccount && !account && <section className="panel empty-state">Selecione um cliente para consultar a conta ou cadastre um novo.</section>}
      </div>
    </div>
  );
}
