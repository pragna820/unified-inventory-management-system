
import { useEffect, useState } from "react";
import "./App.css";

const API = "http://127.0.0.1:8000";

function App() {
  const [inventory, setInventory] = useState([]);
  const [products, setProducts] = useState([]);
  const [skus, setSkus] = useState([]);
  const [locations, setLocations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [saving, setSaving] = useState(false);

  const [product, setProduct] = useState({
    product_id: "",
    name: "",
    category: "",
    brand: "",
    description: "",
  });

  const [movement, setMovement] = useState({
    sku_id: "",
    location_id: "",
    movement_type: "RECEIPT",
    quantity: "1",
  });

  async function loadData() {
    setLoading(true);
    setError("");

    try {
      const paths = ["/inventory", "/products", "/skus", "/locations"];
      const responses = await Promise.all(
        paths.map((path) => fetch(`${API}${path}`))
      );

      if (responses.some((response) => !response.ok)) {
        throw new Error("Unable to load data from the backend.");
      }

      const data = await Promise.all(
        responses.map((response) => response.json())
      );

      setInventory(data[0]);
      setProducts(data[1]);
      setSkus(data[2]);
      setLocations(data[3]);
    } catch {
      setError("Cannot connect to the backend. Check that FastAPI is running.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  async function submitProduct(event) {
    event.preventDefault();
    setSaving(true);
    setMessage("");
    setError("");

    try {
      const response = await fetch(`${API}/products`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(product),
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(
          typeof result.detail === "string"
            ? result.detail
            : JSON.stringify(result.detail || result)
        );
      }

      setMessage("Product created successfully!");
      setProduct({
        product_id: "",
        name: "",
        category: "",
        brand: "",
        description: "",
      });
      await loadData();
    } catch (err) {
      setError(err.message || "Could not create product.");
    } finally {
      setSaving(false);
    }
  }

  async function submitMovement(event) {
    event.preventDefault();
    setSaving(true);
    setMessage("");
    setError("");

    try {
      const response = await fetch(`${API}/inventory/movements`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          sku_id: movement.sku_id,
          location_id: movement.location_id,
          movement_type: movement.movement_type,
          quantity: Number(movement.quantity),
          idempotency_key:
            `ui-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
        }),
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(
          typeof result.detail === "string"
            ? result.detail
            : JSON.stringify(result.detail || result)
        );
      }

      setMessage(
        `Stock movement recorded. New on-hand quantity: ${
          result.on_hand_qty ?? "updated"
        }`
      );
      await loadData();
    } catch (err) {
      setError(err.message || "Could not record stock movement.");
    } finally {
      setSaving(false);
    }
  }

  const totalAvailable = inventory.reduce(
    (sum, item) => sum + Number(item.available_qty || 0),
    0
  );

  const totalOnHand = inventory.reduce(
    (sum, item) => sum + Number(item.on_hand_qty || 0),
    0
  );

  const totalReserved = inventory.reduce(
    (sum, item) => sum + Number(item.reserved_qty || 0),
    0
  );

  const totalBlocked = inventory.reduce(
    (sum, item) => sum + Number(item.blocked_qty || 0),
    0
  );

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">U</div>
          <div>
            <h2>Unified</h2>
            <span>Inventory System</span>
          </div>
        </div>

        <p className="nav-heading">WORKSPACE</p>
        <a className="nav-item active" href="#dashboard">▦ &nbsp; Dashboard</a>
        <a className="nav-item" href="#inventory">▤ &nbsp; Inventory</a>
        <a className="nav-item" href="#products">□ &nbsp; Products</a>
        <a className="nav-item" href="#locations">⌖ &nbsp; Locations</a>

        <div className="sidebar-footer">
          <div className="status-dot" />
          <div>
            <strong>Inventory API</strong>
            <span>Connected when requests succeed</span>
          </div>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar" id="dashboard">
          <div>
            <span className="eyebrow">OVERVIEW</span>
            <h1>Inventory Dashboard</h1>
            <p className="subtitle">
              Manage products and stock in one place.
            </p>
          </div>
          <button className="refresh-button" onClick={loadData}>
            ↻ &nbsp; Refresh data
          </button>
        </header>

        {error && <div className="error-message">{error}</div>}
        {message && <div className="success-message">{message}</div>}

        <section className="stats-grid">
          <article className="stat-card">
            <div className="stat-top">Total Products <span className="stat-icon purple">▣</span></div>
            <strong>{loading ? "—" : products.length}</strong>
            <small>Registered products</small>
          </article>
          <article className="stat-card">
            <div className="stat-top">SKUs <span className="stat-icon blue">◇</span></div>
            <strong>{loading ? "—" : skus.length}</strong>
            <small>Product variants</small>
          </article>
          <article className="stat-card">
            <div className="stat-top">Locations <span className="stat-icon orange">⌖</span></div>
            <strong>{loading ? "—" : locations.length}</strong>
            <small>Warehouses and stores</small>
          </article>
          <article className="stat-card">
            <div className="stat-top">Available Units <span className="stat-icon green">↗</span></div>
            <strong>{loading ? "—" : totalAvailable.toLocaleString()}</strong>
            <small>Units available to sell</small>
          </article>
        </section>

        <section className="panel" id="products">
          <div className="panel-header">
            <div>
              <h2>Add a Product</h2>
              <p>Create a product record in your database.</p>
            </div>
          </div>

          <form className="form-grid" onSubmit={submitProduct}>
            <label>
              Product ID *
              <input
                required
                value={product.product_id}
                placeholder="e.g. PROD001"
                onChange={(e) =>
                  setProduct({ ...product, product_id: e.target.value })
                }
              />
            </label>
            <label>
              Product Name *
              <input
                required
                value={product.name}
                placeholder="e.g. Cotton T-Shirt"
                onChange={(e) =>
                  setProduct({ ...product, name: e.target.value })
                }
              />
            </label>
            <label>
              Category
              <input
                value={product.category}
                placeholder="e.g. Clothing"
                onChange={(e) =>
                  setProduct({ ...product, category: e.target.value })
                }
              />
            </label>
            <label>
              Brand
              <input
                value={product.brand}
                placeholder="e.g. ABC"
                onChange={(e) =>
                  setProduct({ ...product, brand: e.target.value })
                }
              />
            </label>
            <label className="full-width">
              Description
              <input
                value={product.description}
                placeholder="Optional product description"
                onChange={(e) =>
                  setProduct({ ...product, description: e.target.value })
                }
              />
            </label>
            <div className="full-width">
              <button className="refresh-button" type="submit" disabled={saving}>
                {saving ? "Saving..." : "+ Create Product"}
              </button>
            </div>
          </form>
        </section>

        <section className="panel">
          <div className="panel-header">
            <div>
              <h2>Record Stock Movement</h2>
              <p>Receive stock or record a sale for an existing SKU.</p>
            </div>
          </div>

          <form className="form-grid" onSubmit={submitMovement}>
            <label>
              SKU *
              <select
                required
                value={movement.sku_id}
                onChange={(e) =>
                  setMovement({ ...movement, sku_id: e.target.value })
                }
              >
                <option value="">Select a SKU</option>
                {skus.map((sku) => (
                  <option key={sku.sku_id} value={sku.sku_id}>
                    {sku.sku_id}
                  </option>
                ))}
              </select>
            </label>

            <label>
              Location *
              <select
                required
                value={movement.location_id}
                onChange={(e) =>
                  setMovement({ ...movement, location_id: e.target.value })
                }
              >
                <option value="">Select a location</option>
                {locations.map((location) => (
                  <option key={location.location_id} value={location.location_id}>
                    {location.name} ({location.location_id})
                  </option>
                ))}
              </select>
            </label>

            <label>
              Movement Type *
              <select
                value={movement.movement_type}
                onChange={(e) =>
                  setMovement({ ...movement, movement_type: e.target.value })
                }
              >
                <option value="RECEIPT">Stock Receipt</option>
                <option value="SALE">Sale</option>
              </select>
            </label>

            <label>
              Quantity *
              <input
                required
                type="number"
                min="1"
                step="1"
                value={movement.quantity}
                onChange={(e) =>
                  setMovement({ ...movement, quantity: e.target.value })
                }
              />
            </label>

            <div className="full-width">
              <button
                className="refresh-button"
                type="submit"
                disabled={saving || skus.length === 0 || locations.length === 0}
              >
                {saving ? "Saving..." : "Submit Stock Movement"}
              </button>
              {(skus.length === 0 || locations.length === 0) && (
                <p className="form-hint">
                  Create a SKU and location first to record stock.
                </p>
              )}
            </div>
          </form>
        </section>

        <section className="panel" id="inventory">
          <div className="panel-header">
            <div>
              <h2>Current Inventory</h2>
              <p>Stock levels across your locations.</p>
            </div>
            <span className="record-count">{inventory.length} records</span>
          </div>

          {loading ? (
            <div className="empty-state">Loading inventory...</div>
          ) : inventory.length === 0 ? (
            <div className="empty-state">No inventory records found yet.</div>
          ) : (
            <div className="table-wrapper">
              <table>
                <thead>
                  <tr>
                    <th>PRODUCT</th>
                    <th>SKU</th>
                    <th>LOCATION</th>
                    <th>ON HAND</th>
                    <th>RESERVED</th>
                    <th>AVAILABLE</th>
                    <th>STATUS</th>
                  </tr>
                </thead>
                <tbody>
                  {inventory.map((item, index) => (
                    <tr key={`${item.sku_id}-${item.location_id}-${index}`}>
                      <td><strong>{item.product_name}</strong></td>
                      <td>{item.sku_id}</td>
                      <td>{item.location_name}</td>
                      <td>{item.on_hand_qty}</td>
                      <td>{item.reserved_qty}</td>
                      <td><strong>{item.available_qty}</strong></td>
                      <td>
                        <span className={`status-badge ${Number(item.available_qty) > 0 ? "in-stock" : "out-stock"}`}>
                          {Number(item.available_qty) > 0 ? "In stock" : "Out of stock"}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        <section className="bottom-grid">
          <div className="panel summary-panel">
            <h2>Stock Summary</h2>
            <div className="summary-row"><span>Total units on hand</span><strong>{totalOnHand}</strong></div>
            <div className="summary-row"><span>Reserved units</span><strong>{totalReserved}</strong></div>
            <div className="summary-row"><span>Blocked units</span><strong>{totalBlocked}</strong></div>
          </div>
          <div className="panel summary-panel" id="locations">
            <h2>System Information</h2>
            <div className="summary-row"><span>Frontend</span><strong>React</strong></div>
            <div className="summary-row"><span>Backend</span><strong>FastAPI</strong></div>
            <div className="summary-row"><span>Database</span><strong>PostgreSQL</strong></div>
          </div>
        </section>

        <footer className="footer">
          Unified Inventory Management System
          <span>Inventory overview</span>
        </footer>
      </main>
    </div>
  );
}

export default App;
