import { StrictMode, useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { Activity, ArrowUpRight, Check, ChevronDown, CircleHelp, LogIn, Menu, Search, Settings2, SlidersHorizontal, Sparkles, UserPlus, Wallet, X } from 'lucide-react'
import './styles.css'

function SkylineChart({ candles = [] }) {
  const min = candles.length ? Math.min(...candles.map(item => item.low)) : 0
  const max = candles.length ? Math.max(...candles.map(item => item.high)) : 1
  const points = candles.length ? candles.map((candle, index) => {
    const x = (index / Math.max(candles.length - 1, 1)) * 900
    const y = 260 - ((candle.close - min) / Math.max(max - min, 1)) * 175
    return `${x.toFixed(1)} ${y.toFixed(1)}`
  }) : []
  const livePath = points.length ? `M${points.join(' L')}` : ''
  const liveArea = points.length ? `${livePath} L900 300 L0 300 Z` : ''
  return (
    <div className="skyline-wrap" aria-label="NEPSE skyline price chart">
      <div className="chart-grid" />
      <svg className="skyline" viewBox="0 0 900 300" preserveAspectRatio="none" role="img">
        <defs>
          <linearGradient id="mountainFill" x1="0" x2="0" y1="0" y2="1">
            <stop offset="0%" stopColor="#6C5CE7" stopOpacity="0.46" />
            <stop offset="100%" stopColor="#6C5CE7" stopOpacity="0.02" />
          </linearGradient>
          <linearGradient id="ridgeLine" x1="0" x2="1">
            <stop offset="0%" stopColor="#3DD68C" />
            <stop offset="58%" stopColor="#6C5CE7" />
            <stop offset="100%" stopColor="#E8B44D" />
          </linearGradient>
        </defs>
        <path className="mountain-area" d={liveArea || 'M0 249 L38 236 L70 248 L108 190 L139 232 L176 170 L208 216 L245 100 L279 213 L312 178 L349 226 L387 146 L421 232 L455 204 L492 242 L526 125 L562 229 L597 191 L635 237 L675 90 L710 229 L747 173 L781 218 L820 141 L852 223 L900 186 L900 300 L0 300 Z'} fill="url(#mountainFill)" />
        <path className="mountain-ridge" d={livePath || 'M0 249 L38 236 L70 248 L108 190 L139 232 L176 170 L208 216 L245 100 L279 213 L312 178 L349 226 L387 146 L421 232 L455 204 L492 242 L526 125 L562 229 L597 191 L635 237 L675 90 L710 229 L747 173 L781 218 L820 141 L852 223 L900 186'} fill="none" stroke="url(#ridgeLine)" strokeWidth="3" />
        <g className="candle-marks">
          <path d="M108 190 V245 M101 205 H115" /><path d="M176 170 V231 M169 187 H183" /><path d="M245 100 V220 M237 128 H253" /><path d="M387 146 V228 M379 163 H395" /><path d="M526 125 V231 M518 145 H534" /><path d="M675 90 V230 M667 111 H683" /><path d="M820 141 V222 M812 159 H828" />
        </g>
      </svg>
      <div className="chart-labels"><span>Past</span><span>Generated demo interval</span><span>Latest</span></div>
      <span className="chart-tooltip"><strong>{candles.length ? Number(candles[candles.length - 1].close).toFixed(2) : '—'}</strong><small>{candles.length ? 'GENERATED DEMO OHLCV' : 'WAITING FOR DEMO FEED'}</small></span>
    </div>
  )
}

function Ticker({ items = [] }) {
  const tickerItems = items
  return <div className="ticker" aria-label="Simulated market ticker"><div className="ticker-track">{tickerItems.concat(tickerItems).map((item, index) => <span className="ticker-item" key={`${item.symbol}-${index}`}><b>{item.symbol}</b><span>{item.price}</span><em className={item.direction}>{item.change}</em></span>)}</div></div>
}

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

function clearStoredSession() {
  localStorage.removeItem('nepse_access_token')
  localStorage.removeItem('nepse_refresh_token')
  localStorage.removeItem('nepse_user')
  if (typeof window !== 'undefined') window.dispatchEvent(new Event('nepse:session-expired'))
}

async function apiRequest(path, options = {}) {
  const { token = localStorage.getItem('nepse_access_token'), body, headers = {}, ...requestOptions } = options
  const send = (accessToken) => fetch(API_BASE + path, {
    ...requestOptions,
    headers: { 'Content-Type': 'application/json', ...headers, ...(accessToken ? { Authorization: 'Bearer ' + accessToken } : {}) },
    body: body ? JSON.stringify(body) : undefined,
  })
  let response
  try { response = await send(token) }
  catch { throw new Error('Cannot reach the API at ' + API_BASE + '. Check the API service and VITE_API_URL.') }
  if (response.status === 401 && path !== '/auth/refresh') {
    if (!localStorage.getItem('nepse_refresh_token')) {
      clearStoredSession()
      throw new Error('Your session has expired. Please sign in again.')
    }
    let refreshResponse
    try {
      refreshResponse = await fetch(API_BASE + '/auth/refresh', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ refresh_token: localStorage.getItem('nepse_refresh_token') }) })
    } catch {
      throw new Error('The API is temporarily unreachable. Your session has been kept; please retry.')
    }
    const refreshed = await refreshResponse.json().catch(() => ({}))
    if (!refreshResponse.ok || !refreshed.data?.access_token) {
      clearStoredSession()
      throw new Error('Your session has expired. Please sign in again.')
    }
    localStorage.setItem('nepse_access_token', refreshed.data.access_token)
    try { response = await send(refreshed.data.access_token) }
    catch { throw new Error('The API is temporarily unreachable. Your session has been kept; please retry.') }
  }
  const result = await response.json().catch(() => ({}))
  if (!response.ok) {
    const detail = Array.isArray(result.detail) ? result.detail.map(item => item.msg || 'Invalid input').join('; ') : result.detail
    throw new Error(result.error?.message || detail || 'Request failed.')
  }
  return result.data
}

function AuthModal({ mode, onClose, onAuthenticated }) {
  const [formMode, setFormMode] = useState(mode)
  const [form, setForm] = useState({ name: '', username: '', email: '', password: '' })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const submit = async (event) => {
    event.preventDefault(); setError(''); setBusy(true)
    try {
      const data = await apiRequest(`/auth/${formMode === 'login' ? 'login' : 'register'}`, { method: 'POST', body: formMode === 'login' ? { email: form.email, password: form.password } : form })
      localStorage.setItem('nepse_access_token', data.access_token)
      localStorage.setItem('nepse_refresh_token', data.refresh_token)
      localStorage.setItem('nepse_user', JSON.stringify(data.user))
      onAuthenticated(data.user)
    } catch (requestError) { setError(requestError.message) } finally { setBusy(false) }
  }
  return <div className="modal-backdrop" role="dialog" aria-modal="true"><div className="auth-modal"><button className="modal-close" onClick={onClose} aria-label="Close"><X size={18} /></button><p className="eyebrow"><span className="pulse-dot" /> NEPSE / PAPER TRADER</p><h2>{formMode === 'login' ? 'Welcome back.' : 'Start your practice.'}</h2><p className="modal-copy">{formMode === 'login' ? 'Sign in to your paper-trading terminal.' : 'Create an account and receive NPR 1,000,000 in virtual capital.'}</p><form onSubmit={submit}>{formMode === 'register' && <><label>Full name<input required value={form.name} onChange={event => setForm({ ...form, name: event.target.value })} /></label><label>Username<input required value={form.username} onChange={event => setForm({ ...form, username: event.target.value })} /></label></>}<label>Email<input required type="email" value={form.email} onChange={event => setForm({ ...form, email: event.target.value })} /></label><label>Password<input required type="password" minLength="8" value={form.password} onChange={event => setForm({ ...form, password: event.target.value })} /></label>{error && <p className="form-error">{error}</p>}<button className="primary-button form-submit" disabled={busy}>{formMode === 'login' ? <LogIn size={16} /> : <UserPlus size={16} />}{busy ? 'Working...' : formMode === 'login' ? 'Sign in' : 'Create account'}</button></form><button className="switch-auth" onClick={() => { setFormMode(formMode === 'login' ? 'register' : 'login'); setError('') }}>{formMode === 'login' ? 'Need an account? Create one' : 'Already have an account? Sign in'}</button></div></div>
}

function AdminPanel() {
  const [users, setUsers] = useState([])
  const [error, setError] = useState('')
  const [saved, setSaved] = useState('')
  const token = localStorage.getItem('nepse_access_token')
  useEffect(() => { apiRequest('/admin/users', { token }).then(setUsers).catch(requestError => setError(requestError.message)) }, [token])
  const toggleUser = async (user) => { setError(''); setSaved(''); try { const updated = await apiRequest(`/admin/users/${user.id}`, { method: 'PATCH', token, body: { is_active: !user.is_active } }); setUsers(users.map(item => item.id === updated.id ? updated : item)); setSaved(`${updated.username} status saved.`) } catch (requestError) { setError(requestError.message) } }
  return <section className="admin-page"><div className="admin-heading"><div><p className="eyebrow"><span className="pulse-dot" /> ADMIN CONSOLE</p><h1>Keep the market <span>honest.</span></h1><p className="hero-copy">Manage account access and review who can use the paper-trading simulation.</p></div><div className="admin-stat"><span>Registered accounts</span><strong className="metric-number">{users.length}</strong></div></div><div className="panel admin-users"><div className="panel-heading compact"><div><p className="eyebrow">ACCOUNT DIRECTORY</p><h2>User access</h2></div><span className="admin-note"><Check size={14} /> Changes are audit-logged</span></div>{error && <p className="form-error admin-message">{error}</p>}{saved && <p className="saved-message">{saved}</p>}<div className="admin-table"><div className="table-head"><span>USER</span><span>ROLE</span><span>CREATED</span><span>STATUS</span><span>ACTION</span></div>{users.map(user => <div className="admin-row" key={user.id}><span><b>{user.name}</b><small>{user.email}</small></span><span className="mono">{user.role}</span><span className="mono">{new Date(user.created_at).toLocaleDateString()}</span><span className={user.is_active ? 'positive' : 'negative'}>{user.is_active ? 'ACTIVE' : 'SUSPENDED'}</span><button className="status-button" onClick={() => toggleUser(user)}>{user.is_active ? 'Suspend' : 'Reactivate'}</button></div>)}</div></div></section>
}

function MarketsPage({ onSelect, watchlist = [] }) {
  const [query, setQuery] = useState('')
  const [onlyGainers, setOnlyGainers] = useState(false)
  const filtered = watchlist.filter(item => (item.symbol + ' ' + item.name).toLowerCase().includes(query.toLowerCase()) && (!onlyGainers || item.direction === 'up'))
  return <section className="app-page"><div className="page-heading"><div><p className="eyebrow"><span className="pulse-dot" /> SIMULATED MARKET</p><h1>Find your <span>next move.</span></h1><p className="hero-copy">Explore a small sample of clearly labeled simulated NEPSE instruments. Select one to open its generated demo chart.</p></div><span className="data-badge">SIMULATED FEED</span></div><div className="market-tools"><label className="search-field"><Search size={16} /><input placeholder="Search symbol or company" value={query} onChange={event => setQuery(event.target.value)} /></label><button className={onlyGainers ? 'filter-button active-filter' : 'filter-button'} onClick={() => setOnlyGainers(!onlyGainers)}><SlidersHorizontal size={15} /> {onlyGainers ? 'Gainers only' : 'All stocks'}</button></div><div className="market-grid">{filtered.map(item => <button className="market-card panel" key={item.symbol} onClick={() => onSelect(item.symbol)}><div className="market-card-top"><span className="company-badge">{item.symbol[0]}</span><span className="market-change"><em className={item.direction}>{item.change}</em></span></div><p className="eyebrow">{item.symbol}</p><h2>{item.name}</h2><strong className="metric-number">NPR {item.price}</strong><div className="mini-chart"><span className={item.direction} /></div><small>View chart <ArrowUpRight size={13} /></small></button>)}</div>{filtered.length === 0 && <div className="empty-state panel"><Search size={22} /><h2>No matching stocks</h2><p>Try a symbol such as NABIL or NICA.</p></div>}</section>
}

function PortfolioPage({ user }) {
  const [portfolio, setPortfolio] = useState(null)
  const [error, setError] = useState('')
  useEffect(() => { if (user) apiRequest('/portfolio', { token: localStorage.getItem('nepse_access_token') }).then(setPortfolio).catch(requestError => setError(requestError.message)) }, [user])
  if (!user) return <section className="app-page"><div className="empty-state panel"><Wallet size={22} /><h2>Sign in to view your portfolio</h2><p>Your virtual balance and positions are private to your account.</p></div></section>
  const cash = portfolio?.cash_balance ?? 0
  const total = portfolio?.total_value ?? 0
  const positions = portfolio?.positions || []
  
  return <section className="app-page"><div className="page-heading"><div><p className="eyebrow">CAPITAL / OVERVIEW</p><h1>Your practice <span>portfolio.</span></h1><p className="hero-copy">A clear view of virtual capital, allocation, and performance. Nothing here touches real securities.</p></div><span className="data-badge">DATABASE PORTFOLIO</span></div>{error && <p className="form-error">{error}</p>}<div className="portfolio-summary"><div className="panel balance-card"><span>Net portfolio value</span><strong className="metric-number">{portfolio ? "NPR " + Number(total).toLocaleString('en-US', { minimumFractionDigits: 2 }) : "Loading…"}</strong><em className="positive">Persisted account value</em></div><div className="panel balance-card"><span>Unrealized P&amp;L</span><strong className={Number(portfolio?.unrealized_pl || 0) >= 0 ? "metric-number positive" : "metric-number negative"}>{Number(portfolio?.unrealized_pl || 0) < 0 ? "-" : ""}NPR {Math.abs(Number(portfolio?.unrealized_pl || 0)).toLocaleString('en-US', { minimumFractionDigits: 2 })}</strong><small>{portfolio ? positions.length + " open positions" : "Loading account…"}</small></div><div className="panel balance-card"><span>Cash available</span><strong className="metric-number">{portfolio ? "NPR " + Number(cash).toLocaleString('en-US', { minimumFractionDigits: 2 }) : "Loading…"}</strong><small>Available buying power</small></div></div><div className="portfolio-layout"><div className="panel allocation-panel"><div className="panel-heading compact"><div><p className="eyebrow">POSITIONS</p><h2>Capital at work</h2></div></div><div className="position-table">{positions.length ? positions.map(position => <div className="position-row" key={position.symbol}><span><b>{position.symbol}</b><small>{position.company_name}</small></span><span className="mono">{position.quantity}</span><span className="mono">{Number(position.average_price).toFixed(2)}</span><span className="mono">{Number(position.current_price).toFixed(2)}</span><span className={Number(position.unrealized_pl) >= 0 ? "positive mono" : "negative mono"}>{Number(position.unrealized_pl).toFixed(2)}</span></div>) : <div className="empty-state"><p>No positions yet. Place a paper order to begin.</p></div>}</div></div><div className="panel performance-panel"><p className="eyebrow">ACCOUNT LEDGER</p><h2>Realized P&amp;L</h2><strong className={Number(portfolio?.realized_pl || 0) >= 0 ? "metric-number positive" : "metric-number negative"}>{portfolio ? (Number(portfolio.realized_pl) < 0 ? "-" : "") + "NPR " + Math.abs(Number(portfolio.realized_pl)).toLocaleString('en-US', { minimumFractionDigits: 2 }) : "Loading…"}</strong><p className="performance-note">All orders and cash movements are stored in the backend database.</p></div></div></section>
}

function OrdersPage({ user, onSignIn, watchlist = [] }) {
  const [side, setSide] = useState('BUY')
  const [symbol, setSymbol] = useState('NABIL')
  const [quantity, setQuantity] = useState('10')
  const [orders, setOrders] = useState([])
  const [error, setError] = useState('')
  useEffect(() => { if (user) apiRequest('/orders', { token: localStorage.getItem('nepse_access_token') }).then(setOrders).catch(requestError => setError(requestError.message)) }, [user])
  const submitOrder = async event => { event.preventDefault(); if (!user) { onSignIn(); return } setError(''); try { const order = await apiRequest('/orders', { method: 'POST', token: localStorage.getItem('nepse_access_token'), body: { symbol, side, quantity: Number(quantity), order_type: 'MARKET' } }); setOrders([order, ...orders]); setQuantity('10') } catch (requestError) { setError(requestError.message) } }
  return <section className="app-page"><div className="page-heading"><div><p className="eyebrow"><span className="pulse-dot" /> PAPER EXECUTION</p><h1>Make a <span>practice order.</span></h1><p className="hero-copy">Orders are simulated, validated, and persisted in your virtual portfolio database.</p></div><span className="data-badge">DATABASE ORDERS</span></div>{error && <p className="form-error">{error}</p>}<div className="order-layout"><form className="panel order-ticket" onSubmit={submitOrder}><div className="panel-heading compact"><div><p className="eyebrow">ORDER TICKET</p><h2>New order</h2></div></div><div className="segmented"><button type="button" className={side === 'BUY' ? 'segment-active buy-segment' : ''} onClick={() => setSide('BUY')}>Buy</button><button type="button" className={side === 'SELL' ? 'segment-active sell-segment' : ''} onClick={() => setSide('SELL')}>Sell</button></div><label>Instrument<select value={symbol} onChange={event => setSymbol(event.target.value)}>{watchlist.map(item => <option key={item.symbol}>{item.symbol}</option>)}</select></label><label>Quantity<input type="number" min="1" required value={quantity} onChange={event => setQuantity(event.target.value)} /></label><div className="ticket-total"><span>Gross estimate (before fees)</span><strong className="metric-number">NPR {(Number(quantity || 0) * Number(watchlist.find(item => item.symbol === symbol)?.price || 0)).toLocaleString('en-US', { minimumFractionDigits: 2 })}</strong></div><button className={side === 'BUY' ? 'primary-button form-submit' : 'sell-button form-submit'} type="submit">{user ? (side === 'BUY' ? 'Place buy order' : 'Place sell order') : 'Sign in to place order'} <ArrowUpRight size={15} /></button><small className="ticket-disclaimer">Simulation only. Fees are added at execution; no real trade is placed.</small></form><div className="panel order-history"><div className="panel-heading compact"><div><p className="eyebrow">ACTIVITY LEDGER</p><h2>Recent orders</h2></div><span className="admin-note"><Check size={14} /> Database saved</span></div><div className="order-list">{orders.map(order => <div className="order-row" key={order.id}><span><b>{order.symbol} <em className={order.side === 'BUY' ? 'positive' : 'negative'}>{order.side}</em></b><small>{order.id.slice(0, 8)} / {order.quantity} shares</small></span><span className="mono">NPR {Number(order.average_fill_price || 0).toFixed(2)}</span><span className={order.status === 'FILLED' ? 'positive' : 'gold-text'}>{order.status}</span></div>)}</div></div></div></section>
}

function App() {
  const [activeNav, setActiveNav] = useState('Overview')
  const [selected, setSelected] = useState('')
  const [menuOpen, setMenuOpen] = useState(false)
  const [clock, setClock] = useState('15:00:00')
  const [candles, setCandles] = useState([])
  const [watchlist, setWatchlist] = useState([])
  const [authMode, setAuthMode] = useState(null)
  const [user, setUser] = useState(() => { try { return JSON.parse(localStorage.getItem('nepse_user') || 'null') } catch { localStorage.removeItem('nepse_user'); return null } })
  const [dashboardPortfolio, setDashboardPortfolio] = useState(null)

  useEffect(() => {
    const handleSessionExpired = () => { setUser(null); setDashboardPortfolio(null); setActiveNav('Overview') }
    window.addEventListener('nepse:session-expired', handleSessionExpired)
    return () => window.removeEventListener('nepse:session-expired', handleSessionExpired)
  }, [])

  useEffect(() => {
    const timer = setInterval(() => setClock(new Date().toLocaleTimeString('en-GB', { timeZone: 'Asia/Kathmandu' })), 1000)
    return () => clearInterval(timer)
  }, [])

  useEffect(() => {
    apiRequest('/market/stocks').then(rows => {
      const quotes = rows.map(item => {
        const change = Number(item.change_pct || 0)
        return { symbol: item.symbol, name: item.company_name, price: Number(item.current_price).toFixed(2), change: (change >= 0 ? '+' : '') + change.toFixed(2) + '%', direction: change >= 0 ? 'up' : 'down' }
      })
      setWatchlist(quotes)
      setSelected(current => current || quotes[0]?.symbol || '')
    }).catch(() => setWatchlist([]))
  }, [])

  useEffect(() => {
    if (!user) { setDashboardPortfolio(null); return }
    apiRequest('/portfolio').then(setDashboardPortfolio).catch(() => setDashboardPortfolio(null))
  }, [user, activeNav])

  useEffect(() => {
    if (!selected) { setCandles([]); return }
    apiRequest(`/market/stocks/${selected}/prices`).then(data => setCandles(data.candles)).catch(() => setCandles([]))
  }, [selected])

  return (
    <div className="app-shell">
      <Ticker items={watchlist} />
      <header className="topbar">
        <button className="menu-button" aria-label="Open navigation" onClick={() => setMenuOpen(!menuOpen)}><Menu size={20} /></button>
        <a className="brand" href="#top"><span className="brand-mark">N</span><span>NEPSE<span className="brand-slash">/</span></span><small>PAPER TRADER</small></a>
        <nav className={menuOpen ? 'main-nav open' : 'main-nav'}>{['Overview', 'Markets', 'Portfolio', 'Orders', ...(user?.role === 'ADMIN' ? ['Admin'] : [])].map(item => <button className={activeNav === item ? 'nav-active' : ''} key={item} onClick={() => { setActiveNav(item); setMenuOpen(false) }}>{item}</button>)}</nav>
        <div className="top-actions"><button className="icon-button" aria-label="Browse markets" title="Browse markets" onClick={() => setActiveNav("Markets")}><Search size={18} /></button>{user ? <button className="avatar" aria-label="Log out" onClick={() => { localStorage.removeItem('nepse_access_token'); localStorage.removeItem('nepse_refresh_token'); localStorage.removeItem('nepse_user'); setUser(null); setActiveNav('Overview') }}>{user.username?.slice(0, 2).toUpperCase() || 'ME'}</button> : <><button className="auth-link" onClick={() => setAuthMode('login')}>Sign in</button><button className="primary-button compact-button" onClick={() => setAuthMode('register')}><UserPlus size={14} /> Join</button></>}</div>
      </header>

      <main id="top">{activeNav === 'Admin' && user?.role === 'ADMIN' ? <AdminPanel /> : activeNav === 'Markets' ? <MarketsPage watchlist={watchlist} onSelect={symbol => { setSelected(symbol); setActiveNav('Overview') }} /> : activeNav === 'Portfolio' ? <PortfolioPage user={user} /> : activeNav === 'Orders' ? <OrdersPage user={user} watchlist={watchlist} onSignIn={() => setAuthMode('login')} /> : <>
        <section className="hero-intro reveal-one"><div><p className="eyebrow"><span className="pulse-dot" /> DEMO MARKET FEED <span className="mono">{clock} NPT</span></p><h1>Trade the <span>mountains.</span></h1><p className="hero-copy">A focused paper-trading terminal for the Nepal Stock Exchange. Practice with NPR 1,000,000 in virtual capital.</p></div><button className="primary-button" onClick={() => setActiveNav('Markets')}><Sparkles size={16} /> Explore markets <ChevronDown size={15} /></button></section>

        <section className="metric-strip reveal-two"><div><span>Portfolio value</span><strong className="metric-number">{!user ? "Sign in to view" : dashboardPortfolio ? "NPR " + Number(dashboardPortfolio.total_value).toLocaleString("en-US", { minimumFractionDigits: 2 }) : "Loading…"}</strong><small>Persisted virtual account value</small></div><div><span>Available cash</span><strong className="metric-number">{dashboardPortfolio ? "NPR " + Number(dashboardPortfolio.cash_balance).toLocaleString("en-US", { minimumFractionDigits: 2 }) : "—"}</strong><small>Virtual buying power</small></div><div><span>Open positions</span><strong className="metric-number">{dashboardPortfolio ? dashboardPortfolio.positions.length : "—"}</strong><small>Persisted holdings</small></div><div className="signature-metric"><span>Market data mode</span><strong><Activity size={17} /> DEMO</strong><small>Simulated quotes only</small></div></section>

        <section className="workspace reveal-three"><div className="chart-panel panel"><div className="panel-heading"><div><p className="eyebrow">MARKET PULSE / {selected}</p><h2>{watchlist.find(item => item.symbol === selected)?.name || 'Loading demo quote…'}</h2></div><div className="chart-value"><strong className="metric-number">{watchlist.find(item => item.symbol === selected)?.price || '—'}</strong><em className={watchlist.find(item => item.symbol === selected)?.direction || ''}>{watchlist.find(item => item.symbol === selected)?.change || '—'}</em></div></div><SkylineChart candles={candles} /><div className="chart-footer"><span className="chart-legend"><i /> {candles.length ? 'Generated 5-minute demo candles' : 'Simulated market data'} <CircleHelp size={14} /></span></div></div>
          <aside className="watch-panel panel"><div className="panel-heading compact"><div><p className="eyebrow">YOUR RADAR</p><h2>Watchlist</h2></div><button className="icon-button" onClick={() => setActiveNav('Markets')} aria-label="Filter watchlist"><SlidersHorizontal size={17} /></button></div><div className="watch-list">{watchlist.map(item => <button className={selected === item.symbol ? 'watch-row active-row' : 'watch-row'} key={item.symbol} onClick={() => setSelected(item.symbol)}><span className="company-badge">{item.symbol.slice(0, 1)}</span><span className="company-name"><b>{item.symbol}</b><small>{item.name}</small></span><span className="watch-price"><b className="mono">{item.price}</b><em className={item.direction}>{item.change}</em></span></button>)}</div><button className="text-button" onClick={() => setActiveNav('Markets')}>View all markets <ArrowUpRight size={15} /></button></aside></section>

        <section className="lower-grid reveal-four"><div className="panel positions-panel"><div className="panel-heading compact"><div><p className="eyebrow">CAPITAL AT WORK</p><h2>Open positions</h2></div><button className="text-button" onClick={() => setActiveNav('Portfolio')}>Manage <ArrowUpRight size={15} /></button></div><div className="position-table"><div className="table-head"><span>ASSET</span><span>QTY</span><span>AVG. PRICE</span><span>LAST PRICE</span><span>UNREALIZED P&amp;L</span></div>{dashboardPortfolio?.positions?.length ? dashboardPortfolio.positions.slice(0, 3).map(position => <div className="position-row" key={position.symbol}><span><b>{position.symbol}</b><small>{position.company_name}</small></span><span className="mono">{position.quantity}</span><span className="mono">{Number(position.average_price).toFixed(2)}</span><span className="mono">{Number(position.current_price).toFixed(2)}</span><span className={Number(position.unrealized_pl) >= 0 ? "positive mono" : "negative mono"}>{Number(position.unrealized_pl).toFixed(2)}</span></div>) : <div className="empty-state"><p>{user ? "No open positions yet. Place a paper order to begin." : "Sign in to view your persisted positions and actual P&amp;L."}</p></div>}</div></div><div className="panel insight-panel"><div className="insight-icon"><Wallet size={19} /></div><p className="eyebrow">TRADER'S NOTE</p><h2>Consistency compounds.</h2><p>Review your simulated orders, track your virtual positions, and compare your decisions over time. No real securities are traded.</p><button className="secondary-button" onClick={() => setActiveNav('Orders')}>Review your orders <ArrowUpRight size={15} /></button></div></section>
      </>}</main>
      <footer><span>NEPSE PAPER TRADER <i /> SIMULATION ONLY</span><span>Made by Rijan Adhikari <i /> <a className="contact-link" href="mailto:business.rijan.np@gmail.com">business.rijan.np@gmail.com</a></span><span><Settings2 size={14} /> System nominal</span></footer>
      {!user && <button className="floating-auth" onClick={() => setAuthMode('login')}><LogIn size={15} /> Sign in to trade</button>}
      {authMode && <AuthModal mode={authMode} onClose={() => setAuthMode(null)} onAuthenticated={authenticatedUser => { setUser(authenticatedUser); setAuthMode(null) }} />}
    </div>
  )
}

createRoot(document.getElementById('root')).render(<StrictMode><App /></StrictMode>)
