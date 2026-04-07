import React, { useEffect, useState } from "react";
import "./App.css";

// --- SUB-COMPONENT: PRODUCT CARD ---
function ProductCard({ product, onAddToCart, onSelect }) {
  const [tempQty, setTempQty] = useState(1);

  return (
    <div className="product-card">
      <div className="img-frame" onClick={() => onSelect(product)}>
        <img 
          src={`http://127.0.0.1:8000/static/${product.image_path}`} 
          alt={product.name} 
          className="zoom-effect" 
        />
      </div>
      <h3>{product.name}</h3>
      <p>₦{parseFloat(product.price).toLocaleString()}</p>
      
      <div className="qty-input-container" style={{ display: 'flex', gap: '8px', marginTop: '10px' }}>
        <input 
          type="number" 
          min="1" 
          value={tempQty} 
          onChange={(e) => setTempQty(parseInt(e.target.value) || 1)}
          style={{ width: '50px', padding: '5px', textAlign: 'center', borderRadius: '4px', border: '1px solid #ccc' }}
        />
        <button 
          className="add-btn" 
          onClick={() => onAddToCart(product, tempQty)}
          style={{ flex: 1 }}
        >
          Add {tempQty > 1 ? `(${tempQty})` : ""}
        </button>
      </div>
    </div>
  );
}

function App() {
  // --- 1. CORE STATES ---
  const [products, setProducts] = useState([]);
  const [category, setCategory] = useState("food");
  const [cart, setCart] = useState(() => {
    const savedCart = localStorage.getItem("shop_cart_data");
    return savedCart ? JSON.parse(savedCart) : [];
  });
  
  const [cartOpen, setCartOpen] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [view, setView] = useState("grid"); 
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [activeImage, setActiveImage] = useState(null); // For Selective Pictures
  const [isSuccess, setIsSuccess] = useState(false);
  const [orderId, setOrderId] = useState("");

  const [user, setUser] = useState(null); 
  const [authMode, setAuthMode] = useState("login"); 
  const [authData, setAuthData] = useState({ phone: "", password: "" });
  const [giftCardCode, setGiftCardCode] = useState("");
  const [discount, setDiscount] = useState(0);

  const [trackingData, setTrackingData] = useState(null);
  const [trackInput, setTrackInput] = useState("");
  const [userOrders, setUserOrders] = useState([]); 

  // --- 2. EFFECTS ---
  useEffect(() => {
    localStorage.setItem("shop_cart_data", JSON.stringify(cart));
  }, [cart]);

  useEffect(() => {
    fetch("http://127.0.0.1:8000/api/products/")
      .then((res) => res.json())
      .then((data) => setProducts(data))
      .catch((err) => console.error("Error fetching products:", err));
  }, []);

  useEffect(() => {
    if (view === "account" && user) {
      fetch(`http://127.0.0.1:8000/api/orders/?userId=${user.id}`)
        .then((res) => res.json())
        .then((data) => {
          let ordersArray = Array.isArray(data) ? data : (data.results || []);
          setUserOrders(ordersArray.sort((a, b) => b.id - a.id));
        })
        .catch((err) => console.error("Error fetching order history:", err));
    }
  }, [view, user]);

  // --- 3. LOGIC FUNCTIONS ---
  const addToCart = (product, qty = 1) => {
    setCart((prevCart) => {
      const existingItem = prevCart.find((item) => item.id === product.id);
      if (existingItem) {
        return prevCart.map((item) =>
          item.id === product.id 
            ? { ...item, quantity: item.quantity + qty } 
            : item
        );
      }
      return [...prevCart, { ...product, quantity: qty }];
    });
  };

  const clearCart = () => { if (window.confirm("Empty cart?")) setCart([]); };

  const handleAuth = async (e) => {
    e.preventDefault();
    const url = authMode === "login" ? "http://127.0.0.1:8000/api/login/" : "http://127.0.0.1:8000/api/register/";
    try {
      const response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username: authData.phone,
          email: `${authData.phone}@lekki-market.com`,
          password: authData.password
        }),
      });
      const data = await response.json();
      if (response.ok) {
        setUser({ id: data.user_id, phone: authData.phone });
        setView("grid");
      } else {
        alert(data.error || "Authentication failed");
      }
    } catch (err) {
      alert("Backend connection failed.");
    }
  };

  const applyGiftCard = () => {
    if (!user) return alert("Please login to redeem gift cards!");
    if (giftCardCode.toUpperCase() === "EOY2026") {
        setDiscount(5000);
        alert("₦5,000 Discount Applied!");
    } else {
        alert("Invalid Code.");
    }
  };

  const verifyPaymentOnBackend = async (reference, djangoOrderId) => {
    try {
      const response = await fetch("http://localhost:8001/api/payments/verify", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reference, order_id: djangoOrderId }),
      });
      if (response.ok) {
        setIsSuccess(true);
        setCart([]);
        localStorage.removeItem("shop_cart_data");
        window.open(`http://localhost:8001/api/invoices/generate?order_id=${djangoOrderId}`, "_blank");
      }
    } catch (err) {
      console.error("Verification error", err);
    }
  };

  const checkoutWithPaystack = async () => {
    if (cart.length === 0) return alert("Cart is empty!");
    setIsProcessing(true);
    try {
      const response = await fetch("http://127.0.0.1:8000/api/orders/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          items: cart.map((item) => ({ id: parseInt(item.id), quantity: item.quantity })),
          total: totalDue.toFixed(2),
          userId: user ? user.id : "guest_001",
        }),
      });
      const orderData = await response.json();
      setOrderId(orderData.id);

      const handler = window.PaystackPop.setup({
        key: 'pk_live_21207f639d252b46e35e171dca6b075f79cba433', 
        email: user ? `${user.phone}@lekki-market.com` : 'guest@lekki.com',
        amount: Math.round(totalDue * 100), 
        currency: 'NGN',
        onClose: () => setIsProcessing(false),
        callback: (res) => {
          setIsProcessing(false);
          verifyPaymentOnBackend(res.reference, orderData.id);
        }
      });
      handler.openIframe();
    } catch (err) {
      alert("Checkout failed.");
      setIsProcessing(false);
    }
  };

  const handleTrackOrder = async () => {
    if (!trackInput) return alert("Please enter an Order ID");
    try {
      const response = await fetch(`http://127.0.0.1:8000/api/orders/${trackInput}/`);
      const data = await response.json();
      if (response.ok) setTrackingData(data);
      else alert("Order not found.");
    } catch (err) { alert("Connection failed."); }
  };

  // --- 4. CALCULATIONS (SHIPPING REMOVED) ---
  const subTotalValue = cart.reduce((sum, item) => sum + (parseFloat(item.price) * item.quantity), 0);
  const totalDue = Math.max(0, subTotalValue - discount);

  const filteredProducts = products.filter((p) => 
    p.category.toLowerCase() === category.toLowerCase() && 
    p.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // --- 5. RENDER ---
  return (
    <div className="app-grid-wrapper">
      <header>
        <h1>1-Stop Shop</h1>
        <div className="header-adv-frame">
          <img src="http://127.0.0.1:8000/static/Shoping-ad.jpg" alt="Advertisement" className="adv-banner" />
        </div>
        <div className="search-bar">
          <input type="text" placeholder="Search products..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} />
        </div>
        <button className="cart-toggle" onClick={() => setCartOpen(!cartOpen)}>
          🛒 Cart ({cart.reduce((acc, item) => acc + item.quantity, 0)})
        </button>
      </header>

      <nav className="main-nav">
        <ul>
          <li><button className="nav-btn-link" onClick={() => { setView("grid"); setSelectedProduct(null); setIsSuccess(false); }}>Home</button></li>
          <li><button className="nav-btn-link" onClick={() => { setView("tracking"); setTrackingData(null); }}>Track Order</button></li>
          <li><button className="nav-btn-link" onClick={() => setView("account")}>Account</button></li>
          <li className="nav-auth">
            {user ? (
              <div className="user-badge"><span className="user-welcome">Hi, <strong>{user.phone}</strong></span></div>
            ) : (
              <button className="register-link" onClick={() => { setView("auth"); setAuthMode("register"); }}>Register / Login</button>
            )}
          </li>
        </ul>
      </nav>

      <aside className="left-sidebar">
        <h3>Categories</h3>
        <nav className="side-nav">
          {["food", "electronics", "office", "style&fashion", "sex-toys", "rent-house", "car-sales", "kitchen-items"].map((catId) => (
            <button key={catId} className={category === catId ? "active" : ""} 
              onClick={() => { setCategory(catId); setView("grid"); setSelectedProduct(null); }}>
              {catId.toUpperCase()}
            </button>
          ))}
        </nav>
      </aside>

      <main>
        {view === "auth" ? (
          <div className="view-container auth-screen">
             <div className="auth-card">
               <h1>{authMode === "login" ? "Welcome Back" : "Create Account"}</h1>
               <form onSubmit={handleAuth} className="auth-form">
                  <div className="form-group">
                    <label>Phone Number</label>
                    <input type="tel" placeholder="Enter your phone number" required value={authData.phone} onChange={(e) => setAuthData({...authData, phone: e.target.value})} />
                  </div>
                  <div className="form-group">
                    <label>Password</label>
                    <input type="password" placeholder="Enter your password" required value={authData.password} onChange={(e) => setAuthData({...authData, password: e.target.value})} />
                  </div>
                  <button type="submit" className="auth-submit-btn">{authMode === "login" ? "Login" : "Register"}</button>
               </form>
               <p className="auth-toggle-text" onClick={() => setAuthMode(authMode === "login" ? "register" : "login")}>
                 {authMode === "login" ? "New here? Create an account" : "Already have an account? Login"}
               </p>
             </div>
          </div>
        ) : view === "tracking" ? (
          <div className="view-container tracking-screen">
            <h1>📦 Track Your Shipment</h1>
            <div className="track-search-box">
              <input type="text" placeholder="Enter Order ID" value={trackInput} onChange={(e) => setTrackInput(e.target.value)} />
              <button onClick={handleTrackOrder}>Check Status</button>
            </div>
            {trackingData && (
              <div className="tracking-timeline">
                <div className="step active"><div className="info"><strong>Status: {trackingData.status}</strong></div></div>
              </div>
            )}
            <button className="back-btn" onClick={() => setView("grid")}>Back</button>
          </div>
        ) : view === "account" ? (
          <div className="view-container account-screen">
            <h1>Order History</h1>
            <div className="order-history">
              {userOrders.map((order) => (
                <div key={order.id} className="history-item">
                  <strong>Order #{order.id}</strong>
                  <span>₦{parseFloat(order.total_price || 0).toLocaleString()}</span>
                  <button onClick={() => window.open(`http://localhost:8001/api/invoices/generate?order_id=${order.id}`, "_blank")}>PDF</button>
                </div>
              ))}
            </div>
          </div>
        ) : isSuccess ? (
          <div className="view-container success-screen">
            <h2>✅ Payment Confirmed!</h2>
            <button onClick={() => setIsSuccess(false)}>Continue Shopping</button>
          </div>
        ) : selectedProduct ? (
          <div className="view-container detail-screen">
            <button onClick={() => { setSelectedProduct(null); setActiveImage(null); }}>← Back</button>
            
            <div className="detail-layout" style={{ display: 'flex', gap: '30px', marginTop: '20px' }}>
              {/* LEFT: IMAGE GALLERY */}
              <div className="image-gallery-container" style={{ flex: 1 }}>
                <div className="main-image-frame">
                  <img 
                    src={`http://127.0.0.1:8000/static/${activeImage || selectedProduct.image_path}`} 
                    alt={selectedProduct.name} 
                    style={{ width: "100%", borderRadius: "12px", border: '1px solid #ddd' }} 
                  />
                </div>
                
                <div className="thumbnail-row" style={{ display: 'flex', gap: '10px', marginTop: '15px', overflowX: 'auto' }}>
                  {/* Base Image Thumbnail */}
                  <img 
                    src={`http://127.0.0.1:8000/static/${selectedProduct.image_path}`}
                    onClick={() => setActiveImage(selectedProduct.image_path)}
                    style={{ width: '60px', height: '60px', cursor: 'pointer', borderRadius: '4px', border: activeImage === selectedProduct.image_path ? '2px solid #2e7d32' : '1px solid #ccc' }}
                  />
                  {/* Selective Pictures (Additional) */}
                  {selectedProduct.additional_images?.map((img, idx) => (
                    <img 
                      key={idx}
                      src={`http://127.0.0.1:8000/static/${img.path}`}
                      onClick={() => setActiveImage(img.path)}
                      style={{ width: '60px', height: '60px', cursor: 'pointer', borderRadius: '4px', border: activeImage === img.path ? '2px solid #2e7d32' : '1px solid #ccc' }}
                    />
                  ))}
                </div>
              </div>

              {/* RIGHT: PRODUCT INFO */}
              <div className="detail-info" style={{ flex: 1 }}>
                <h1>{selectedProduct.name}</h1>
                <h2 style={{ color: '#2e7d32' }}>₦{parseFloat(selectedProduct.price).toLocaleString()}</h2>
                <p className="description">{selectedProduct.description || "Premium quality product."}</p>
                <button className="add-btn" style={{ padding: '15px 30px', fontSize: '1.1rem' }} onClick={() => addToCart(selectedProduct)}>
                  Add to Cart
                </button>
              </div>
            </div>
          </div>
        ) : (
          <div className="product-grid">
            {filteredProducts.map((p) => (
              <ProductCard key={p.id} product={p} onAddToCart={addToCart} onSelect={setSelectedProduct} />
            ))}
          </div>
        )}
      </main>

      <aside className={`right-sidebar ${cartOpen ? "open" : ""}`}>
        <div className="cart-container">
          <h3>Your Cart</h3>
          <div className="cart-items-list">
            {cart.map((item, index) => (
              <div key={index} className="cart-item-row">
                <div className="cart-item-info">
                  <strong>{item.name} (x{item.quantity})</strong>
                  <span>₦{(parseFloat(item.price) * item.quantity).toLocaleString()}</span>
                </div>
                <button onClick={() => setCart(cart.filter((_, i) => i !== index))}>×</button>
              </div>
            ))}
            {cart.length === 0 && <p>Your bag is empty.</p>}
          </div>

          <div className="gift-card-input-wrapper">
             <input type="text" placeholder="EOY Gift Code" value={giftCardCode} onChange={(e) => setGiftCardCode(e.target.value)} />
             <button onClick={applyGiftCard}>Apply</button>
          </div>

          <div className="total-section">
            <p>Subtotal: ₦{subTotalValue.toLocaleString()}</p>
            <p className="final-total">Total: <strong>₦{totalDue.toLocaleString()}</strong></p>
            <button className="vendor-btn paystack" disabled={isProcessing} onClick={checkoutWithPaystack}>
              {isProcessing ? "Processing..." : "Pay Now"}
            </button>
            <button className="clear-cart-btn" onClick={clearCart}>Clear Cart</button>
          </div>
        </div>
      </aside>
    </div>
  );
}

export default App;