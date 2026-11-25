function money(value) {
  return Number(value || 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

function dateTime(value) {
  if (!value) return "—";
  const hasTimezone = /(?:Z|[+-]\d{2}:?\d{2})$/i.test(value);
  return new Date(hasTimezone ? value : `${value}Z`).toLocaleString("pt-BR");
}

function dateOnly(value) {
  if (!value) return "—";
  return new Date(`${value}T12:00:00`).toLocaleDateString("pt-BR");
}

function paymentLabel(payment) {
  return [payment.payment_method, payment.installments > 1 ? `${payment.installments}x` : ""]
    .filter(Boolean).join(" ");
}

export default function SalePrintout({ sale, mode, storeName }) {
  if (!sale || !mode) return null;
  const credit = sale.credit;
  const customer = credit?.customer;

  return (
    <div id="sale-print-root" className={`sale-print-root print-${mode}`}>
      {mode === "receipt" && (
        <article className="print-document print-receipt">
          <h1>{storeName || "StockFlow"}</h1>
          <h2>Comprovante de venda</h2>
          <p>Venda #{sale.id}</p>
          <p>Data: {dateTime(sale.created_at)}</p>
          <p>Vendedor(a): {sale.seller_name || "Não informado"}</p>
          <hr />
          <h3>Pagamento</h3>
          {(sale.payments || []).map(payment => (
            <div className="print-line" key={payment.id || payment.payment_method}>
              <span>{paymentLabel(payment)}</span><strong>{money(payment.amount)}</strong>
            </div>
          ))}
          <hr />
          <div className="print-line print-total"><span>Total da venda</span><strong>{money(sale.total)}</strong></div>
          <p className="print-thanks">Obrigado pela preferência!</p>
        </article>
      )}

      {mode === "installments" && credit && (
        credit.installments.map(installment => (
          <article className="print-document print-installment" key={installment.number}>
            <h1>{storeName || "StockFlow"}</h1>
            <h2>Parcela de crediário</h2>
            <div className="print-installment-number">{installment.number}/{credit.installments.length}</div>
            <p><strong>Cliente:</strong> {customer.full_name} · #{customer.id}</p>
            <p><strong>CPF:</strong> {customer.cpf}</p>
            <p><strong>Telefone:</strong> {customer.phone || "—"}</p>
            <p><strong>Venda:</strong> #{sale.id} · {dateTime(sale.created_at)}</p>
            <div className="print-installment-amount">
              <span>Valor da parcela</span><strong>{money(installment.amount)}</strong>
            </div>
            <div className="print-installment-due">
              <span>Vencimento</span><strong>{dateOnly(installment.due_date)}</strong>
            </div>
            <p className="print-installment-seller">Atendido por: {sale.seller_name || "Não informado"}</p>
          </article>
        ))
      )}

      {mode === "store-copy" && credit && (
        <article className="print-document print-store-copy">
          <h1>{storeName || "StockFlow"}</h1>
          <h2>Resumo da venda no crediário · Via da loja</h2>
          <p><strong>Venda:</strong> #{sale.id} · <strong>Data:</strong> {dateTime(sale.created_at)}</p>
          <p><strong>Vendedor(a):</strong> {sale.seller_name || "Não informado"}</p>
          <p><strong>Cliente:</strong> {customer.full_name} · #{customer.id}</p>
          <p><strong>CPF:</strong> {customer.cpf} · <strong>Telefone:</strong> {customer.phone || "—"}</p>
          <p><strong>Endereço:</strong> {customer.address}</p>
          <h3>Itens da venda</h3>
          <table>
            <thead><tr><th>Produto</th><th>Qtd.</th><th>Unitário</th><th>Total</th></tr></thead>
            <tbody>{(sale.items || []).map(item => (
              <tr key={item.id || item.product_name}>
                <td>{item.product_name}</td><td>{item.quantity}</td><td>{money(item.unit_price)}</td><td>{money(item.subtotal)}</td>
              </tr>
            ))}</tbody>
          </table>
          <div className="print-line"><span>Subtotal</span><strong>{money(sale.gross_total)}</strong></div>
          <div className="print-line"><span>Desconto</span><strong>{money(sale.discount)}</strong></div>
          <div className="print-line print-total"><span>Total da venda</span><strong>{money(sale.total)}</strong></div>
          <h3>Condições do crediário</h3>
          <div className="print-line"><span>Entrada</span><strong>{money((sale.payments || []).filter(payment => payment.payment_method !== "Crediário").reduce((sum, payment) => sum + Number(payment.amount), 0))}</strong></div>
          <div className="print-line"><span>Saldo financiado</span><strong>{money(credit.installments.reduce((sum, installment) => sum + Number(installment.amount), 0))}</strong></div>
          <table className="print-schedule-table">
            <thead><tr><th>Parcela</th><th>Vencimento</th><th>Valor</th></tr></thead>
            <tbody>{credit.installments.map(installment => (
              <tr key={installment.number}>
                <td>{installment.number}/{credit.installments.length}</td><td>{dateOnly(installment.due_date)}</td><td>{money(installment.amount)}</td>
              </tr>
            ))}</tbody>
          </table>
          <div className="print-signatures">
            <div><span>Assinatura do(a) cliente</span></div>
            <div><span>Assinatura do(a) responsável pela loja</span></div>
          </div>
        </article>
      )}
    </div>
  );
}
