import { useEffect, useState } from "react";
import axios from "axios";
import {
  LayoutDashboard, Package, ArrowLeftRight, Wallet,
  Plus, RefreshCw, Search, TrendingUp, TrendingDown,
  Boxes, AlertTriangle, Menu, X, ShoppingCart, Trash2, Receipt, Store, Upload, CreditCard
} from "lucide-react";
import "./App.css";
import CreditPage from "./CreditPage.jsx";

const API = "http://localhost:8000";

function localDateKey(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
}

function App() {
  const [page, setPage] = useState("dashboard");
  const [products, setProducts] = useState([]);
  const [cash, setCash] = useState([]);
  const [sales, setSales] = useState([]);
  const [storeProfile, setStoreProfile] = useState({ store_name: "StockFlow", has_logo: false, logo_url: "" });
  const [logoFile, setLogoFile] = useState(null);
  const [logoPreview, setLogoPreview] = useState("");
  const [removeLogo, setRemoveLogo] = useState(false);
  const [savingStore, setSavingStore] = useState(false);
  const [storeMessage, setStoreMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [saleSearch, setSaleSearch] = useState("");
  const [cart, setCart] = useState([]);
  const [discount, setDiscount] = useState("0");
  const [discountType, setDiscountType] = useState("value");
  const [paymentMethod, setPaymentMethod] = useState("Pix");
  const [cardInstallments, setCardInstallments] = useState(1);
  const [creditCustomerId, setCreditCustomerId] = useState("");
  const [creditInstallmentCount, setCreditInstallmentCount] = useState(3);
  const [creditPaidNowCount, setCreditPaidNowCount] = useState(0);
  const [creditUpfrontMethod, setCreditUpfrontMethod] = useState("Pix");
  const [sellerName, setSellerName] = useState("");
  const [dashboardFilters, setDashboardFilters] = useState({ from: "", to: "", product: "", seller: "" });
  const [savingSale, setSavingSale] = useState(false);
  const [manualItem, setManualItem] = useState({ name: "", quantity: 1, price: "" });

  const [productForm, setProductForm] = useState({
    name: "", sku: "", category: "", description: "",
    price: "", stock: 0, min_stock: 0
  });

  const [stockForm, setStockForm] = useState({
    product_id: "", movement_type: "entrada",
    quantity: 1, description: ""
  });

  const [cashForm, setCashForm] = useState({
    movement_type: "entrada", description: "",
    category: "Venda", amount: "", payment_method: "Pix"
  });

  async function loadData() {
    setLoading(true);
    setError("");
    try {
      const [p, c, s, profile] = await Promise.allSettled([
        axios.get(`${API}/products`),
        axios.get(`${API}/cash/movements`),
        axios.get(`${API}/sales`),
        axios.get(`${API}/store/profile`)
      ]);

      if (p.status === "fulfilled") {
        setProducts(Array.isArray(p.value.data) ? p.value.data : []);
      } else {
        throw p.reason;
      }

      if (c.status === "fulfilled") {
        setCash(Array.isArray(c.value.data) ? c.value.data : []);
      } else {
        setCash([]);
      }

      if (s.status === "fulfilled") {
        setSales(Array.isArray(s.value.data) ? s.value.data : []);
      } else {
        setSales([]);
      }
      if (profile.status === "fulfilled") {
        const data = profile.value.data;
        setStoreProfile({
          ...data,
          logo_url: data.has_logo ? `${API}/store/logo?v=${encodeURIComponent(data.updated_at || "")}` : ""
        });
      }
    } catch (err) {
      setError("Não foi possível carregar os produtos. Verifique se o backend está funcionando.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => () => {
    if (logoPreview.startsWith("blob:")) URL.revokeObjectURL(logoPreview);
  }, [logoPreview]);

  async function saveStoreProfile(e) {
    e.preventDefault();
    const formData = new FormData();
    formData.append("store_name", storeProfile.store_name.trim());
    formData.append("remove_logo", String(removeLogo));
    if (logoFile) formData.append("logo", logoFile);
    setSavingStore(true);
    setStoreMessage("");
    try {
      const { data } = await axios.put(`${API}/store/profile`, formData);
      setStoreProfile({
        ...data,
        logo_url: data.has_logo ? `${API}/store/logo?v=${encodeURIComponent(data.updated_at || Date.now())}` : ""
      });
      setLogoFile(null);
      setLogoPreview("");
      setRemoveLogo(false);
      setStoreMessage("Dados da loja salvos.");
    } catch (err) {
      alert(err.response?.data?.detail || "Não foi possível salvar os dados da loja.");
    } finally {
      setSavingStore(false);
    }
  }

  async function createProduct(e) {
    e.preventDefault();
    try {
      await axios.post(`${API}/products`, {
        ...productForm,
        price: productForm.price ? Number(productForm.price) : null,
        stock: Number(productForm.stock),
        min_stock: Number(productForm.min_stock)
      });
      setShowForm(false);
      setProductForm({
        name: "", sku: "", category: "", description: "",
        price: "", stock: 0, min_stock: 0
      });
      await loadData();
    } catch (err) {
      alert(err.response?.data?.detail || "Erro ao cadastrar produto.");
    }
  }

  async function createStockMovement(e) {
    e.preventDefault();
    try {
      await axios.post(`${API}/stock/movements`, {
        ...stockForm,
        product_id: Number(stockForm.product_id),
        quantity: Number(stockForm.quantity)
      });
      setShowForm(false);
      setStockForm({
        product_id: "", movement_type: "entrada",
        quantity: 1, description: ""
      });
      await loadData();
    } catch (err) {
      alert(err.response?.data?.detail || "Erro ao registrar movimentação.");
    }
  }

  async function createCashMovement(e) {
    e.preventDefault();
    try {
      await axios.post(`${API}/cash/movements`, {
        ...cashForm,
        amount: Number(cashForm.amount)
      });
      setShowForm(false);
      setCashForm({
        movement_type: "entrada", description: "",
        category: "Venda", amount: "", payment_method: "Pix"
      });
      await loadData();
    } catch (err) {
      alert(err.response?.data?.detail || "Erro ao registrar movimentação financeira.");
    }
  }

  const totalUnits = products.reduce((sum, p) => sum + Number(p.stock || 0), 0);
  const lowStock = products.filter(p => Number(p.stock || 0) <= Number(p.min_stock || 0));
  const income = cash.filter(m => m.movement_type === "entrada")
    .reduce((sum, m) => sum + Number(m.amount || 0), 0);
  const expenses = cash.filter(m => m.movement_type === "saida")
    .reduce((sum, m) => sum + Number(m.amount || 0), 0);
  const balance = income - expenses;

  const money = value => Number(value || 0).toLocaleString("pt-BR", {
    style: "currency", currency: "BRL"
  });

  const filteredProducts = products.filter(p =>
    `${p.name} ${p.sku || ""} ${p.category || ""}`
      .toLowerCase().includes(search.toLowerCase())
  );

  const saleProducts = products.filter(p =>
    Number(p.stock || 0) > 0 &&
    `${p.name} ${p.sku || ""} ${p.category || ""}`
      .toLowerCase().includes(saleSearch.toLowerCase())
  );

  const cartSubtotal = cart.reduce(
    (sum, item) => sum + Number(item.price) * Number(item.quantity), 0
  );
  const discountInput = Math.max(0, Number(discount) || 0);
  const saleDiscount = Math.min(
    cartSubtotal,
    Number((discountType === "percent"
      ? cartSubtotal * Math.min(discountInput, 100) / 100
      : discountInput).toFixed(2))
  );
  const saleTotal = Math.max(0, Number((cartSubtotal - saleDiscount).toFixed(2)));
  const normalizedCreditCount = Math.max(1, Math.min(120, Math.floor(Number(creditInstallmentCount) || 1)));
  const creditTotalCents = Math.round(saleTotal * 100);
  const creditBaseCents = Math.floor(creditTotalCents / normalizedCreditCount);
  const creditRemainderCents = creditTotalCents % normalizedCreditCount;
  const creditScheduleAmounts = Array.from({ length: normalizedCreditCount }, (_, index) =>
    (creditBaseCents + (index < creditRemainderCents ? 1 : 0)) / 100
  );
  const normalizedPaidNowCount = Math.max(0, Math.min(normalizedCreditCount - 1, Math.floor(Number(creditPaidNowCount) || 0)));
  const creditUpfrontAmount = Number(creditScheduleAmounts.slice(0, normalizedPaidNowCount).reduce((sum, amount) => sum + amount, 0).toFixed(2));
  const creditBalanceAmount = Number((saleTotal - creditUpfrontAmount).toFixed(2));

  const dashboardSales = sales.filter(sale => {
    const saleDate = localDateKey(sale.created_at);
    const sellerMatches = !dashboardFilters.seller ||
      (sale.seller_name || "Não informado").toLowerCase() === dashboardFilters.seller.toLowerCase();
    const productMatches = !dashboardFilters.product ||
      (sale.items || []).some(item => item.product_name === dashboardFilters.product);
    return (!dashboardFilters.from || saleDate >= dashboardFilters.from) &&
      (!dashboardFilters.to || saleDate <= dashboardFilters.to) &&
      sellerMatches && productMatches;
  });
  const dashboardRevenue = dashboardSales.reduce((sum, sale) => sum + Number(sale.total || 0), 0);
  const dashboardUnits = dashboardSales.reduce((sum, sale) => sum + (sale.items || []).reduce((n, item) => n + Number(item.quantity || 0), 0), 0);
  const dashboardProducts = [...new Set(sales.flatMap(sale => (sale.items || []).map(item => item.product_name)).filter(Boolean))].sort();
  const dashboardSellers = [...new Set(sales.map(sale => sale.seller_name || "Não informado"))].sort();
  const productPerformance = Object.values(dashboardSales.flatMap(sale => sale.items || []).reduce((acc, item) => {
    const name = item.product_name || "Item avulso";
    acc[name] = acc[name] || { name, quantity: 0, total: 0 };
    acc[name].quantity += Number(item.quantity || 0);
    acc[name].total += Number(item.subtotal || 0);
    return acc;
  }, {})).sort((a, b) => b.total - a.total).slice(0, 6);
  const sellerPerformance = Object.values(dashboardSales.reduce((acc, sale) => {
    const name = sale.seller_name || "Não informado";
    acc[name] = acc[name] || { name, count: 0, total: 0 };
    acc[name].count += 1;
    acc[name].total += Number(sale.total || 0);
    return acc;
  }, {})).sort((a, b) => b.total - a.total);
  const dailyPerformance = Object.entries(dashboardSales.reduce((acc, sale) => {
    const day = localDateKey(sale.created_at) || "Sem data";
    acc[day] = (acc[day] || 0) + Number(sale.total || 0);
    return acc;
  }, {})).sort(([a], [b]) => a.localeCompare(b)).slice(-10);

  const navItems = [
    { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
    { id: "store", label: "Minha loja", icon: Store },
    { id: "products", label: "Produtos", icon: Package },
    { id: "stock", label: "Estoque", icon: ArrowLeftRight },
    { id: "sales", label: "Vendas", icon: ShoppingCart },
    { id: "credit", label: "Crediário", icon: CreditCard },
    { id: "cash", label: "Caixa", icon: Wallet }
  ];

  function openForm() {
    setShowForm(true);
  }

  function addToCart(product) {
    setCart(current => {
      const found = current.find(item => item.product_id === product.id);
      if (found) {
        if (found.quantity >= Number(product.stock || 0)) {
          alert("Não há quantidade suficiente desse produto no estoque.");
          return current;
        }
        return current.map(item => item.product_id === product.id
          ? { ...item, quantity: item.quantity + 1 }
          : item
        );
      }
      return [...current, {
        product_id: product.id,
        name: product.name,
        sku: product.sku,
        price: Number(product.price || 0),
        stock: Number(product.stock || 0),
        quantity: 1
      }];
    });
  }

  function changeCartQuantity(productId, nextQuantity) {
    const product = productId == null ? null : products.find(p => p.id === productId);
    const quantity = Number(nextQuantity);
    if (!Number.isInteger(quantity) || quantity < 1) return;
    if (product && quantity > Number(product.stock || 0)) {
      alert("A quantidade não pode ser maior que o estoque disponível.");
      return;
    }
    setCart(current => current.map(item =>
      (item.product_id ?? item.cart_key) === productId ? { ...item, quantity } : item
    ));
  }

  function removeFromCart(cartKey) {
    setCart(current => current.filter(item => (item.product_id ?? item.cart_key) !== cartKey));
  }

  function addManualItem(e) {
    e.preventDefault();
    const name = manualItem.name.trim();
    const quantity = Number(manualItem.quantity);
    const price = Number(manualItem.price);
    if (!name || !Number.isInteger(quantity) || quantity < 1 || !Number.isFinite(price) || price <= 0) {
      alert("Informe nome, quantidade válida e preço maior que zero.");
      return;
    }
    const cartKey = `manual-${Date.now()}`;
    setCart(current => [...current, { cart_key: cartKey, product_id: null, name, price, quantity }]);
    setManualItem({ name: "", quantity: 1, price: "" });
  }

  async function finishSale() {
    if (!sellerName.trim()) {
      alert("Informe o vendedor responsável pela venda.");
      return;
    }
    if (cart.length === 0) {
      alert("Adicione pelo menos um produto ao carrinho.");
      return;
    }
    if (saleTotal <= 0) {
      alert("O total da venda precisa ser maior que zero.");
      return;
    }

    const usingCredit = paymentMethod === "Crediário";
    if (usingCredit && (!Number.isInteger(Number(creditCustomerId)) || Number(creditCustomerId) < 1)) {
      alert("Informe o ID do cliente cadastrado para abrir o crediário.");
      return;
    }
    const payments = usingCredit
      ? [
          ...(creditUpfrontAmount > 0 ? [{
            payment_method: creditUpfrontMethod,
            amount: creditUpfrontAmount,
            installments: creditUpfrontMethod === "Cartão de crédito" ? Number(cardInstallments) : 1,
            fee_amount: 0
          }] : []),
          { payment_method: "Crediário", amount: creditBalanceAmount, installments: normalizedCreditCount, fee_amount: 0 }
        ]
      : [{
          payment_method: paymentMethod,
          amount: saleTotal,
          installments: paymentMethod === "Cartão de crédito" ? Number(cardInstallments) : 1,
          fee_amount: 0
        }];

    const payload = {
      seller_name: sellerName.trim() || "Não informado",
      items: cart.map(item => ({
        product_id: item.product_id,
        ...(item.product_id == null ? { product_name: item.name, unit_price: item.price } : {}),
        quantity: item.quantity
      })),
      discount: saleDiscount,
      payments,
      ...(usingCredit ? { credit_terms: {
        customer_id: Number(creditCustomerId),
        installment_count: normalizedCreditCount,
        paid_now_count: normalizedPaidNowCount,
        upfront_payment_method: creditUpfrontAmount > 0 ? creditUpfrontMethod : null,
        upfront_card_installments: Number(cardInstallments)
      } } : {})
    };

    setSavingSale(true);
    try {
      await axios.post(`${API}/sales`, payload);
      alert("Venda registrada com sucesso!");
      setCart([]);
      setDiscount("0");
      setDiscountType("value");
      setPaymentMethod("Pix");
      setCardInstallments(1);
      setCreditCustomerId("");
      setCreditInstallmentCount(3);
      setCreditPaidNowCount(0);
      setCreditUpfrontMethod("Pix");
      setSaleSearch("");
      await loadData();
    } catch (err) {
      alert(err.response?.data?.detail || "Não foi possível registrar a venda.");
    } finally {
      setSavingSale(false);
    }
  }

  const getSaleTotal = sale => sale.total ?? sale.gross_total ?? sale.amount ?? 0;

  return (
    <div className="app">
      <aside className={`sidebar ${menuOpen ? "sidebar-open" : ""}`}>
        <div className="brand">
          {storeProfile.logo_url ? <img className="store-brand-logo" src={storeProfile.logo_url} alt="" /> : <div className="brand-icon"><Boxes size={24} /></div>}
          <div><strong>{storeProfile.store_name || "StockFlow"}</strong><span>Gestão inteligente</span></div>
          <button className="close-menu" onClick={() => setMenuOpen(false)}><X /></button>
        </div>

        <div className="menu-label">MENU PRINCIPAL</div>
        <nav>
          {navItems.map(item => {
            const Icon = item.icon;
            return (
              <button key={item.id}
                className={`nav-item ${page === item.id ? "active" : ""}`}
                onClick={() => { setPage(item.id); setShowForm(false); setMenuOpen(false); }}>
                <Icon size={19} /> {item.label}
              </button>
            );
          })}
        </nav>

        <div className="sidebar-footer">
          <div className="status-dot" />
          <span>Sistema conectado</span>
        </div>
      </aside>

      <main className="main">
        <header className="topbar">
          <button className="mobile-menu" onClick={() => setMenuOpen(true)}><Menu /></button>
          <div>
            <h1>{navItems.find(n => n.id === page)?.label}</h1>
            <p>Bem-vindo ao seu painel de gestão.</p>
          </div>
          <button className="refresh-button" onClick={loadData}>
            <RefreshCw size={17} /> Atualizar
          </button>
        </header>

        {error && <div className="error-banner">{error}</div>}

        {loading ? (
          <div className="loading">Carregando informações...</div>
        ) : (
          <>
            {page === "dashboard" && (
              <>
                <section className="welcome">
                  <div><h2>Visão geral</h2><p>Acompanhe os principais indicadores da sua operação.</p></div>
                  <span>StockFlow · Painel de controle</span>
                </section>

                <section className="panel dashboard-filters">
                  <div className="panel-heading"><div><h3>Filtros do relatório</h3><p>Filtre vendas e faturamento por data, produto e vendedor.</p></div>
                    <button className="text-button" type="button" onClick={() => setDashboardFilters({ from: "", to: "", product: "", seller: "" })}>Limpar filtros</button>
                  </div>
                  <div className="dashboard-filter-grid">
                    <Field label="De"><input type="date" value={dashboardFilters.from} onChange={e => setDashboardFilters({ ...dashboardFilters, from: e.target.value })} /></Field>
                    <Field label="Até"><input type="date" value={dashboardFilters.to} onChange={e => setDashboardFilters({ ...dashboardFilters, to: e.target.value })} /></Field>
                    <Field label="Produto"><select value={dashboardFilters.product} onChange={e => setDashboardFilters({ ...dashboardFilters, product: e.target.value })}><option value="">Todos os produtos</option>{dashboardProducts.map(name => <option key={name}>{name}</option>)}</select></Field>
                    <Field label="Vendedor"><select value={dashboardFilters.seller} onChange={e => setDashboardFilters({ ...dashboardFilters, seller: e.target.value })}><option value="">Todos os vendedores</option>{dashboardSellers.map(name => <option key={name}>{name}</option>)}</select></Field>
                  </div>
                </section>
                <section className="stats-grid">
                  <Stat icon={<TrendingUp />} label="Faturamento filtrado" value={money(dashboardRevenue)} />
                  <Stat icon={<Receipt />} label="Vendas filtradas" value={dashboardSales.length} />
                  <Stat icon={<Boxes />} label="Unidades vendidas" value={dashboardUnits} />
                  <Stat icon={<Package />} label="Produtos cadastrados" value={products.length} />
                </section>

                <section className="dashboard-grid">
                  <div className="panel"><div className="panel-heading"><div><h3>Faturamento por dia</h3><p>Até os últimos 10 dias com vendas, conforme os filtros.</p></div></div>
                    {dailyPerformance.length === 0 ? <div className="empty-state">Nenhuma venda encontrada.</div> : dailyPerformance.map(([day, total]) => { const max = Math.max(...dailyPerformance.map(([, value]) => value), 1); return <div className="performance-row" key={day}><div className="performance-label"><span>{day === "Sem data" ? day : new Date(`${day}T12:00:00`).toLocaleDateString("pt-BR")}</span><strong>{money(total)}</strong></div><div className="bar-track"><div className="bar-fill" style={{ width: `${Math.max(4, total / max * 100)}%` }} /></div></div>; })}
                  </div>
                  <div className="panel"><div className="panel-heading"><div><h3>Vendas por vendedor</h3><p>Faturamento e quantidade no filtro atual.</p></div></div>
                    {sellerPerformance.length === 0 ? <div className="empty-state">Nenhuma venda encontrada.</div> : sellerPerformance.map(seller => <div className="low-stock-item" key={seller.name}><div><strong>{seller.name}</strong><span>{seller.count} venda(s)</span></div><b>{money(seller.total)}</b></div>)}
                  </div>
                </section>
                <section className="panel"><div className="panel-heading"><div><h3>Produtos mais vendidos</h3><p>Por faturamento no filtro atual.</p></div></div>
                  {productPerformance.length === 0 ? <div className="empty-state">Nenhuma venda encontrada.</div> : <div className="table-wrap"><table><thead><tr><th>Produto / item</th><th>Unidades</th><th>Faturamento</th></tr></thead><tbody>{productPerformance.map(item => <tr key={item.name}><td><strong>{item.name}</strong></td><td>{item.quantity}</td><td><strong>{money(item.total)}</strong></td></tr>)}</tbody></table></div>}
                </section>

                <section className="dashboard-grid">
                  <div className="panel">
                    <div className="panel-heading"><div><h3>Resumo financeiro</h3><p>Movimentações registradas</p></div></div>
                    <div className="finance-line">
                      <div className="finance-icon green"><TrendingUp /></div>
                      <div><span>Entradas</span><strong>{money(income)}</strong></div>
                    </div>
                    <div className="finance-line">
                      <div className="finance-icon red"><TrendingDown /></div>
                      <div><span>Saídas</span><strong>{money(expenses)}</strong></div>
                    </div>
                    <div className="balance-line"><span>Saldo atual</span><strong>{money(balance)}</strong></div>
                  </div>

                  <div className="panel">
                    <div className="panel-heading"><div><h3>Atenção ao estoque</h3><p>Produtos no limite ou abaixo do mínimo</p></div><AlertTriangle color="#d97706" /></div>
                    {lowStock.length === 0 ? (
                      <div className="empty-state">Tudo certo! Nenhum produto com estoque baixo.</div>
                    ) : lowStock.slice(0, 5).map(p => (
                      <div className="low-stock-item" key={p.id}>
                        <div><strong>{p.name}</strong><span>Estoque mínimo: {p.min_stock}</span></div>
                        <b>{p.stock} un.</b>
                      </div>
                    ))}
                  </div>
                </section>

                <section className="panel">
                  <div className="panel-heading"><div><h3>Produtos recentes</h3><p>Visão rápida do cadastro</p></div>
                    <button className="text-button" onClick={() => setPage("products")}>Ver todos</button>
                  </div>
                  <ProductTable products={products.slice(0, 5)} money={money} />
                </section>
              </>
            )}

            {page === "store" && (
              <section className="panel store-settings-panel">
                <div className="panel-heading"><div><h3>Identidade da loja</h3><p>Personalize o nome e o logotipo exibidos no StockFlow.</p></div><Store size={22} /></div>
                <form onSubmit={saveStoreProfile}>
                  <Field label="Nome da loja" required><input required maxLength="150" value={storeProfile.store_name || ""} onChange={e => setStoreProfile({ ...storeProfile, store_name: e.target.value })} placeholder="Ex.: Loja da Maria" /></Field>
                  <Field label="Logotipo (PNG, JPG ou WebP, até 3 MB)">
                    <input type="file" accept="image/png,image/jpeg,image/webp" onChange={e => {
                      const file = e.target.files?.[0] || null;
                      setLogoFile(file);
                      setRemoveLogo(false);
                      setLogoPreview(file ? URL.createObjectURL(file) : "");
                    }} />
                  </Field>
                  {(logoPreview || storeProfile.logo_url) && !removeLogo && <div className="store-logo-preview"><img src={logoPreview || storeProfile.logo_url} alt="Prévia do logotipo da loja" /></div>}
                  {storeProfile.has_logo && !removeLogo && <button type="button" className="text-button store-remove-logo" onClick={() => { setRemoveLogo(true); setLogoFile(null); setLogoPreview(""); }}>Remover logotipo</button>}
                  {removeLogo && <p className="store-feedback">O logotipo será removido ao salvar.</p>}
                  {storeMessage && <p className="store-feedback">{storeMessage}</p>}
                  <button className="primary-button submit-button" type="submit" disabled={savingStore}>
                    <Upload size={17} /> {savingStore ? "Salvando..." : "Salvar dados da loja"}
                  </button>
                </form>
              </section>
            )}

            {page === "credit" && <CreditPage money={money} onDataChanged={loadData} />}

            {page === "products" && (
              <section className="panel">
                <div className="panel-heading">
                  <div><h3>Cadastro de produtos</h3><p>Gerencie os produtos da sua loja.</p></div>
                  <button className="primary-button" onClick={openForm}><Plus size={17} /> Novo produto</button>
                </div>
                <div className="search-box"><Search size={18} /><input placeholder="Buscar produto, SKU ou categoria..." value={search} onChange={e => setSearch(e.target.value)} /></div>
                <ProductTable products={filteredProducts} money={money} />
              </section>
            )}

            {page === "stock" && (
              <section className="panel">
                <div className="panel-heading">
                  <div><h3>Movimentação de estoque</h3><p>Registre entradas e saídas de produtos.</p></div>
                  <button className="primary-button" onClick={openForm}><Plus size={17} /> Movimentar estoque</button>
                </div>
                <ProductTable products={products} money={money} showStock />
              </section>
            )}

            {page === "sales" && (
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 300px), 1fr))", gap: 20, alignItems: "start" }}>
                <section className="panel">
                  <div className="panel-heading">
                    <div><h3>Nova venda</h3><p>Selecione os produtos para adicionar ao carrinho.</p></div>
                    <ShoppingCart size={22} />
                  </div>
                  <div className="search-box">
                    <Search size={18} />
                    <input placeholder="Buscar produto disponível..." value={saleSearch} onChange={e => setSaleSearch(e.target.value)} />
                  </div>
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(190px, 1fr))", gap: 12, marginTop: 16 }}>
                    {saleProducts.map(product => (
                      <button key={product.id} type="button" onClick={() => addToCart(product)}
                        style={{ textAlign: "left", border: "1px solid var(--border, #e5e7eb)", borderRadius: 12, padding: 14, background: "var(--card, #fff)", cursor: "pointer", color: "inherit" }}>
                        <strong style={{ display: "block", marginBottom: 6 }}>{product.name}</strong>
                        <span style={{ display: "block", color: "var(--muted, #6b7280)", fontSize: 12 }}>{product.sku || "Sem SKU"} · {product.stock} em estoque</span>
                        <strong style={{ display: "block", marginTop: 10 }}>{money(product.price)}</strong>
                        <span style={{ display: "inline-flex", alignItems: "center", gap: 5, marginTop: 10, fontSize: 13 }}><Plus size={15} /> Adicionar</span>
                      </button>
                    ))}
                  </div>
                  {saleProducts.length === 0 && <div className="empty-state">Nenhum produto disponível com esse filtro.</div>}
                  <form onSubmit={addManualItem} style={{ display: "grid", gap: 10, marginTop: 20, paddingTop: 18, borderTop: "1px solid var(--border, #e5e7eb)" }}>
                    <strong>Adicionar item sem estoque</strong>
                    <Field label="Nome do item" required><input required maxLength="150" value={manualItem.name} onChange={e => setManualItem({ ...manualItem, name: e.target.value })} /></Field>
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                      <Field label="Quantidade" required><input required type="number" min="1" step="1" value={manualItem.quantity} onChange={e => setManualItem({ ...manualItem, quantity: e.target.value })} /></Field>
                      <Field label="Preço unitário (R$)" required><input required type="number" min="0.01" step="0.01" value={manualItem.price} onChange={e => setManualItem({ ...manualItem, price: e.target.value })} /></Field>
                    </div>
                    <button className="primary-button" type="submit"><Plus size={17} /> Adicionar item avulso</button>
                  </form>
                </section>

                <section className="panel">
                  <div className="panel-heading">
                    <div><h3>Carrinho</h3><p>{cart.reduce((sum, item) => sum + item.quantity, 0)} item(ns)</p></div>
                    <ShoppingCart size={22} />
                  </div>
                  <Field label="Vendedor responsável" required><input required maxLength="150" placeholder="Nome do vendedor" value={sellerName} onChange={e => setSellerName(e.target.value)} /></Field>
                  {cart.length === 0 ? (
                    <div className="empty-state">Adicione produtos para iniciar uma venda.</div>
                  ) : (
                    <div style={{ display: "grid", gap: 14 }}>
                      {cart.map(item => (
                        <div key={item.product_id ?? item.cart_key} style={{ borderBottom: "1px solid var(--border, #e5e7eb)", paddingBottom: 12 }}>
                          <div style={{ display: "flex", justifyContent: "space-between", gap: 8 }}>
                            <strong>{item.name}</strong>
                            <button type="button" onClick={() => removeFromCart(item.product_id ?? item.cart_key)} title="Remover" style={{ border: 0, background: "transparent", cursor: "pointer" }}><Trash2 size={17} /></button>
                          </div>
                          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 10, marginTop: 8 }}>
                            <input aria-label={`Quantidade de ${item.name}`} type="number" min="1" max={item.product_id == null ? undefined : item.stock} value={item.quantity}
                              onChange={e => changeCartQuantity(item.product_id ?? item.cart_key, e.target.value)}
                              style={{ width: 76, padding: 8, border: "1px solid var(--border, #d1d5db)", borderRadius: 8 }} />
                            <span>{money(item.price * item.quantity)}</span>
                          </div>
                          <small style={{ color: "var(--muted, #6b7280)" }}>{money(item.price)} cada · {item.product_id == null ? "sem controle de estoque" : `estoque: ${item.stock}`}</small>
                        </div>
                      ))}
                    </div>
                  )}

                  <div style={{ display: "grid", gap: 12, marginTop: 18 }}>
                    <div style={{ display: "flex", justifyContent: "space-between" }}><span>Subtotal</span><strong>{money(cartSubtotal)}</strong></div>
                    <Field label="Tipo de desconto">
                      <select value={discountType} onChange={e => setDiscountType(e.target.value)}>
                        <option value="value">Valor em reais (R$)</option>
                        <option value="percent">Percentual (%)</option>
                      </select>
                    </Field>
                    <Field label={discountType === "percent" ? "Desconto (%)" : "Desconto (R$)"}>
                      <input type="number" min="0" max={discountType === "percent" ? 100 : undefined} step="0.01" value={discount} onChange={e => setDiscount(e.target.value)} />
                    </Field>
                    <div style={{ display: "flex", justifyContent: "space-between", color: "var(--muted, #6b7280)" }}>
                      <span>Desconto aplicado</span><strong>{money(saleDiscount)}</strong>
                    </div>
                    <Field label="Forma de pagamento">
                      <select value={paymentMethod} onChange={e => setPaymentMethod(e.target.value)}>
                        {["Dinheiro", "Pix", "Cartão de crédito", "Cartão de débito", "Transferência", "Outros", "Crediário"].map(x => <option key={x}>{x}</option>)}
                      </select>
                    </Field>
                    {paymentMethod === "Cartão de crédito" && <Field label="Parcelas no cartão (sem acréscimo)"><input type="number" min="1" max="36" step="1" value={cardInstallments} onChange={e => setCardInstallments(Number(e.target.value) || 1)} /></Field>}
                    {paymentMethod === "Crediário" && <div className="credit-sale-options">
                      <Field label="ID do cliente" required><input required type="number" min="1" step="1" value={creditCustomerId} onChange={e => setCreditCustomerId(e.target.value)} placeholder="Cadastre ou consulte em Crediário" /></Field>
                      <div className="credit-sale-grid">
                        <Field label="Quantidade de parcelas"><input type="number" min="1" max="120" step="1" value={creditInstallmentCount} onChange={e => setCreditInstallmentCount(e.target.value)} /></Field>
                        <Field label="Parcelas pagas agora"><input type="number" min="0" max={normalizedCreditCount - 1} step="1" value={normalizedPaidNowCount} onChange={e => setCreditPaidNowCount(e.target.value)} /></Field>
                      </div>
                      <p className="credit-sale-note">A primeira parcela vence 30 dias após a venda. Juros de 1% ao mês, calculados por dia, somente após o vencimento.</p>
                      {creditUpfrontAmount > 0 && <>
                        <Field label="Forma de pagamento das parcelas pagas agora"><select value={creditUpfrontMethod} onChange={e => setCreditUpfrontMethod(e.target.value)}>{["Dinheiro", "Pix", "Cartão de crédito", "Cartão de débito", "Transferência", "Outros"].map(method => <option key={method}>{method}</option>)}</select></Field>
                        {creditUpfrontMethod === "Cartão de crédito" && <Field label="Parcelas no cartão do pagamento inicial"><input type="number" min="1" max="36" step="1" value={cardInstallments} onChange={e => setCardInstallments(Number(e.target.value) || 1)} /></Field>}
                        <div className="credit-sale-totals"><span>Recebido agora: <strong>{money(creditUpfrontAmount)}</strong></span><span>Saldo no crediário: <strong>{money(creditBalanceAmount)}</strong></span></div>
                      </>}
                    </div>}
                    <div style={{ display: "flex", justifyContent: "space-between", fontSize: 18, paddingTop: 12, borderTop: "1px solid var(--border, #e5e7eb)" }}>
                      <strong>Total</strong><strong>{money(saleTotal)}</strong>
                    </div>
                    <button className="primary-button submit-button" type="button" disabled={savingSale || cart.length === 0} onClick={finishSale}>
                      {savingSale ? "Registrando..." : "Finalizar venda"}
                    </button>
                  </div>
                </section>
              </div>
            )}

            {page === "sales" && (
              <section className="panel" style={{ marginTop: 20 }}>
                <div className="panel-heading">
                  <div><h3>Histórico de vendas</h3><p>Vendas registradas no StockFlow.</p></div>
                  <Receipt size={22} />
                </div>
                <div className="table-wrap">
                  <table>
                    <thead><tr><th>Venda</th><th>Data</th><th>Vendedor</th><th>Pagamento</th><th>Status</th><th>Total</th></tr></thead>
                    <tbody>
                      {sales.map(sale => (
                        <tr key={sale.id}>
                          <td><strong>#{sale.id}</strong></td>
                          <td>{sale.created_at ? new Date(sale.created_at).toLocaleString("pt-BR") : "—"}</td>
                          <td>{sale.seller_name || "Não informado"}</td>
                          <td>{(sale.payments || []).map(payment => [payment.payment_method, payment.installments > 1 ? `${payment.installments}x` : ""].filter(Boolean).join(" ")).join(", ")}</td>
                          <td><span className="tag tag-green">{sale.status || "Concluída"}</span></td>
                          <td><strong>{money(getSaleTotal(sale))}</strong></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {sales.length === 0 && <div className="empty-state">Nenhuma venda encontrada.</div>}
                </div>
              </section>
            )}

            {page === "cash" && (
              <section className="panel">
                <div className="panel-heading">
                  <div><h3>Controle de caixa</h3><p>Entradas, despesas e movimentações financeiras.</p></div>
                  <button className="primary-button" onClick={openForm}><Plus size={17} /> Nova movimentação</button>
                </div>
                <div className="cash-summary">
                  <div><span>Entradas</span><strong className="green-text">{money(income)}</strong></div>
                  <div><span>Saídas</span><strong className="red-text">{money(expenses)}</strong></div>
                  <div><span>Saldo</span><strong>{money(balance)}</strong></div>
                </div>
                <div className="table-wrap"><table><thead><tr><th>Descrição</th><th>Categoria</th><th>Pagamento</th><th>Data</th><th>Tipo</th><th>Valor</th></tr></thead>
                  <tbody>{cash.map(m => <tr key={m.id}>
                    <td><strong>{m.description}</strong></td><td>{m.category || "—"}</td><td>{m.payment_method || "—"}</td>
                    <td>{m.created_at ? new Date(m.created_at).toLocaleDateString("pt-BR") : "—"}</td>
                    <td><span className={`tag ${m.movement_type === "entrada" ? "tag-green" : "tag-red"}`}>{m.movement_type}</span></td>
                    <td><strong>{money(m.amount)}</strong></td>
                  </tr>)}</tbody></table>
                  {cash.length === 0 && <div className="empty-state">Nenhuma movimentação financeira cadastrada.</div>}
                </div>
              </section>
            )}
          </>
        )}
      </main>

      {showForm && (
        <div className="modal-backdrop" onClick={() => setShowForm(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-heading">
              <h2>{page === "products" ? "Novo produto" : page === "stock" ? "Movimentar estoque" : "Movimentação de caixa"}</h2>
              <button onClick={() => setShowForm(false)}><X /></button>
            </div>

            {page === "products" && (
              <form onSubmit={createProduct}>
                <Field label="Nome do produto" required><input required value={productForm.name} onChange={e => setProductForm({...productForm, name: e.target.value})} /></Field>
                <div className="form-row">
                  <Field label="SKU / Código"><input value={productForm.sku} onChange={e => setProductForm({...productForm, sku: e.target.value})} /></Field>
                  <Field label="Categoria"><input value={productForm.category} onChange={e => setProductForm({...productForm, category: e.target.value})} /></Field>
                </div>
                <Field label="Descrição"><textarea value={productForm.description} onChange={e => setProductForm({...productForm, description: e.target.value})} /></Field>
                <div className="form-row">
                  <Field label="Preço (R$)"><input type="number" min="0" step="0.01" value={productForm.price} onChange={e => setProductForm({...productForm, price: e.target.value})} /></Field>
                  <Field label="Estoque inicial"><input type="number" min="0" value={productForm.stock} onChange={e => setProductForm({...productForm, stock: e.target.value})} /></Field>
                  <Field label="Estoque mínimo"><input type="number" min="0" value={productForm.min_stock} onChange={e => setProductForm({...productForm, min_stock: e.target.value})} /></Field>
                </div>
                <button className="primary-button submit-button">Salvar produto</button>
              </form>
            )}

            {page === "stock" && (
              <form onSubmit={createStockMovement}>
                <Field label="Produto" required>
                  <select required value={stockForm.product_id} onChange={e => setStockForm({...stockForm, product_id: e.target.value})}>
                    <option value="">Selecione um produto</option>
                    {products.map(p => <option key={p.id} value={p.id}>{p.name} — estoque: {p.stock}</option>)}
                  </select>
                </Field>
                <Field label="Tipo de movimentação">
                  <select value={stockForm.movement_type} onChange={e => setStockForm({...stockForm, movement_type: e.target.value})}>
                    <option value="entrada">Entrada</option><option value="saida">Saída</option>
                  </select>
                </Field>
                <Field label="Quantidade" required><input type="number" min="1" required value={stockForm.quantity} onChange={e => setStockForm({...stockForm, quantity: e.target.value})} /></Field>
                <Field label="Descrição"><input value={stockForm.description} onChange={e => setStockForm({...stockForm, description: e.target.value})} placeholder="Ex.: Compra de mercadoria" /></Field>
                <button className="primary-button submit-button">Registrar movimentação</button>
              </form>
            )}

            {page === "cash" && (
              <form onSubmit={createCashMovement}>
                <Field label="Tipo">
                  <select value={cashForm.movement_type} onChange={e => setCashForm({...cashForm, movement_type: e.target.value})}>
                    <option value="entrada">Entrada</option><option value="saida">Saída</option>
                  </select>
                </Field>
                <Field label="Descrição" required><input required value={cashForm.description} onChange={e => setCashForm({...cashForm, description: e.target.value})} /></Field>
                <div className="form-row">
                  <Field label="Categoria"><input value={cashForm.category} onChange={e => setCashForm({...cashForm, category: e.target.value})} /></Field>
                  <Field label="Valor (R$)" required><input required type="number" min="0.01" step="0.01" value={cashForm.amount} onChange={e => setCashForm({...cashForm, amount: e.target.value})} /></Field>
                </div>
                <Field label="Forma de pagamento">
                  <select value={cashForm.payment_method} onChange={e => setCashForm({...cashForm, payment_method: e.target.value})}>
                    {["Dinheiro", "Pix", "Cartão de crédito", "Cartão de débito", "Transferência", "Outros"].map(x => <option key={x}>{x}</option>)}
                  </select>
                </Field>
                <button className="primary-button submit-button">Registrar movimentação</button>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function Stat({ icon, label, value }) {
  return <div className="stat-card"><div className="stat-icon">{icon}</div><span>{label}</span><strong>{value}</strong></div>;
}

function Field({ label, required, children }) {
  return <label className="field"><span>{label}{required ? " *" : ""}</span>{children}</label>;
}

function ProductTable({ products, money, showStock = false }) {
  return (
    <div className="table-wrap">
      <table><thead><tr><th>Produto</th><th>SKU</th><th>Categoria</th><th>Preço</th><th>Estoque</th><th>Status</th></tr></thead>
        <tbody>{products.map(p => {
          const low = Number(p.stock || 0) <= Number(p.min_stock || 0);
          return <tr key={p.id}>
            <td><strong>{p.name}</strong></td><td>{p.sku || "—"}</td><td>{p.category || "—"}</td>
            <td>{p.price == null ? "—" : money(p.price)}</td><td>{p.stock ?? 0} un.</td>
            <td><span className={`tag ${low ? "tag-red" : "tag-green"}`}>{low ? "Estoque baixo" : "Normal"}</span></td>
          </tr>;
        })}</tbody>
      </table>
      {products.length === 0 && <div className="empty-state">Nenhum produto encontrado.</div>}
    </div>
  );
}

export default App;
