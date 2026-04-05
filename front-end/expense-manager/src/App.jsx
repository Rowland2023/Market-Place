import React, { useEffect, useState } from "react";
import "./App.css";

function App() {
  const [products, setProducts] = useState([]);
  const [category, setCategory] = useState("food");
  // --- UPDATED CART STATE ---
const [cart, setCart] = useState(() => {
  // Check localStorage for a saved cart
  const savedCart = localStorage.getItem("shop_cart_data");
  // If it exists, parse the JSON string back into an array; otherwise, start empty []
  return savedCart ? JSON.parse(savedCart) : [];
});
  const [cartOpen, setCartOpen] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);

  // VIEW STATES
  const [view, setView] = useState("grid"); 
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [isSuccess, setIsSuccess] = useState(false);
  const [orderId, setOrderId] = useState("");

  // --- AUTH & GIFT CARD STATES ---
  const [user, setUser] = useState(null); 
  const [authMode, setAuthMode] = useState("login"); 
  // Initialized with empty strings to remove any default "Peter" values
  const [authData, setAuthData] = useState({ email: "", password: "" });
  const [giftCardCode, setGiftCardCode] = useState("");
  const [discount, setDiscount] = useState(0);

  // TRACKING & ACCOUNT STATES
  const [trackingData, setTrackingData] = useState(null);
  const [trackInput, setTrackInput] = useState("");
  const [userOrders, setUserOrders] = useState([]); 

  // --- 1. FETCH DATA ---
  // --- SAVE CART TO STORAGE ON EVERY CHANGE ---
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
    if (view === "account") {
      const uid = user ? user.id : "guest_001";
      fetch(`http://127.0.0.1:8000/api/orders/?userId=${uid}`)
        .then((res) => res.json())
        .then((data) => {
          let ordersArray = Array.isArray(data) ? data : (data.results || []);
          setUserOrders(ordersArray.sort((a, b) => b.id - a.id));
        })
        .catch((err) => console.error("Error fetching order history:", err));
    }
  }, [view, user]);

  // --- 2. AUTH LOGIC ---
  const handleAuth = async (e) => {
    e.preventDefault();
    const url = authMode === "login" ? "http://127.0.0.1:8000/api/login/" : "http://127.0.0.1:8000/api/register/";
    
    try {
      const response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username: authData.email,
          email: authData.email,
          password: authData.password
        }),
      });
      const data = await response.json();
      if (response.ok) {
        setUser({ id: data.user_id, email: authData.email });
        setView("grid");
      } else {
        alert(data.error || data.message || "Authentication failed");
      }
    } catch (err) {
      alert("Backend connection failed. Is Django running on port 8000?");
    }
  };

  // --- 3. GIFT CARD LOGIC ---
  const applyGiftCard = () => {
    if (!user) return alert("Please register or login to redeem your Year-End Gift Card!");
    if (giftCardCode.toUpperCase() === "EOY2026") {
       setDiscount(5000);
       alert("Success! ₦5,000 has been deducted from your total.");
    } else {
       alert("Invalid or Expired Gift Card Code.");
    }
  };

  // --- 4. PAYMENT & CHECKOUT ---
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
        setDiscount(0);
        setGiftCardCode("");
        setCartOpen(false);
        window.open(`http://localhost:8001/api/invoices/generate?order_id=${djangoOrderId}`, "_blank");
      }
    } catch (err) {
      console.error("Verification failed", err);
    }
  };

  const checkoutWithPaystack = async () => {
    if (cart.length === 0) return alert("Your cart is empty!");
    if (!window.PaystackPop) return alert("Paystack SDK not loaded.");
    setIsProcessing(true);

    try {
      const response = await fetch("http://127.0.0.1:8000/api/orders/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          items: cart.map((item) => ({ id: parseInt(item.id), quantity: 1 })),
          total: totalDue.toFixed(2),
          userId: user ? user.id : "guest_001",
        }),
      });

      const orderData = await response.json();
      if (!response.ok) throw new Error("Server failed to create order");

      setOrderId(orderData.id);

      const handler = window.PaystackPop.setup({
        key: 'pk_live_21207f639d252b46e35e171dca6b075f79cba433', 
        email: user ? user.email : 'guest@lekki.com',
        amount: Math.round(totalDue * 100), 
        currency: 'NGN',
        onClose: () => setIsProcessing(false),
        callback: (response) => {
  setIsProcessing(false);
  setCart([]); // Clears React State
  localStorage.removeItem("shop_cart_data"); // Clears Browser Memory
  verifyPaymentOnBackend(response.reference, orderData.id);
}
      });
      handler.openIframe();
    } catch (err) {
      alert(`Checkout failed: ${err.message}`);
      setIsProcessing(false);
    }
  };

  // --- 5. UI CALCULATIONS ---
  const subTotalValue = cart.reduce((sum, item) => sum + parseFloat(item.price || 0), 0);
  const shippingFee = cart.length > 0 ? 1500 : 0;
  const totalDue = Math.max(0, subTotalValue + shippingFee - discount);

  const filteredProducts = products.filter((p) => 
    p.category.toLowerCase() === category.toLowerCase() && 
    p.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const addToCart = (product) => setCart([...cart, product]);
  const clearCart = () => { if (window.confirm("Empty cart?")) setCart([]); };

  const handleTrackOrder = async () => {
    if (!trackInput) return alert("Please enter an Order ID");
    try {
      const response = await fetch(`http://127.0.0.1:8000/api/orders/${trackInput}/`);
      const data = await response.json();
      if (response.ok) setTrackingData(data);
      else alert("Order not found.");
    } catch (err) { alert("Connection failed."); }
  };

  // ... your logic/calculations end here (totalDue, filteredProducts, etc.)

  return (
    <div className="app-grid-wrapper">
      {/* PLACE IT RIGHT HERE: */}
      <header>
        <h1>1-Stop Shop</h1>

        {/* --- NEW ADVERT FRAME --- */}
        <div className="header-adv-frame">
          <img 
              /* Pointing to your Django static folder */
            src="http://127.0.0.1:8000/static/Shoping-ad.jpg" 
            alt="Current Advertisement" 
            className="adv-banner"
            onClick={() => window.open('https://your-promo-link.com', '_blank')}
          />
        </div>

        <div className="search-bar">
          <input 
            type="text" 
            placeholder="Search products..." 
            value={searchTerm} 
            onChange={(e) => setSearchTerm(e.target.value)} 
          />
        </div>
        
        <button className="cart-toggle" onClick={() => setCartOpen(!cartOpen)}>
          🛒 Cart ({cart.length})
        </button>
      </header>

      <nav className="main-nav">
        <ul>
          <li><button className="nav-btn-link" onClick={() => { setView("grid"); setSelectedProduct(null); setIsSuccess(false); }}>Home</button></li>
          <li><button className="nav-btn-link" onClick={() => { setView("tracking"); setTrackingData(null); }}>Track Order</button></li>
          <li><button className="nav-btn-link" onClick={() => setView("account")}>Account</button></li>
          <li className="nav-auth">
            {user ? (
              <div className="user-badge">
                <span className="user-welcome">Hi, <strong>{user.email}</strong></span>
              </div>
            ) : (
              <button className="register-link" onClick={() => { setView("auth"); setAuthMode("register"); }}>Register / Login</button>
            )}
          </li>
        </ul>
      </nav>

      <aside className="left-sidebar">
        <h3>Categories</h3>
        <nav className="side-nav">
          {["food", "electronics", "office", "clothing", "sex-toys","rent-house","car-sales","kitchen-items"].map((catId) => (
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
               <p className="auth-subtitle">Register to unlock the EOY ₦5,000 Gift Card!</p>
               <form onSubmit={handleAuth} className="auth-form">
                  <div className="form-group">
                    <label>Email Address</label>
                    <input 
                      type="email" 
                      placeholder="e.g. name@example.com" 
                      required 
                      value={authData.email}
                      onChange={(e) => setAuthData({...authData, email: e.target.value})} 
                    />
                  </div>
                  <div className="form-group">
                    <label>Password</label>
                    <input 
                      type="password" 
                      placeholder="••••••••" 
                      required 
                      value={authData.password}
                      onChange={(e) => setAuthData({...authData, password: e.target.value})} 
                    />
                  </div>
                  <button type="submit" className="auth-submit-btn">
                    {authMode === "login" ? "Login to Shop" : "Complete Registration"}
                  </button>
               </form>
               <p className="auth-toggle-text" onClick={() => setAuthMode(authMode === "login" ? "register" : "login")}>
                 {authMode === "login" ? "New here? Create an account" : "Already have an account? Login"}
               </p>
               <button className="back-btn-secondary" onClick={() => setView("grid")}>Continue as Guest</button>
             </div>
          </div>
        ) : view === "tracking" ? (
          <div className="view-container tracking-screen">
            <h1>📦 Track Your Shipment</h1>
            <div className="track-search-box">
              <input type="text" placeholder="Enter Order ID" className="track-input" value={trackInput} onChange={(e) => setTrackInput(e.target.value)} />
              <button className="track-btn-action" onClick={handleTrackOrder}>Check Status</button>
            </div>
            {trackingData && (
              <div className="tracking-timeline">
                <div className="step completed"><div className="bullet"></div><div className="info"><strong>Order Confirmed</strong><span>#{trackingData.id}</span></div></div>
                <div className="step active"><div className="bullet"></div><div className="info"><strong>Status: {trackingData.status}</strong></div></div>
              </div>
            )}
            <button className="back-btn" onClick={() => setView("grid")}>Back</button>
          </div>
        ) : view === "account" ? (
          <div className="view-container account-screen">
            <h1>Order History</h1>
            <div className="order-history">
              {userOrders.length === 0 ? <p>No orders found.</p> : userOrders.map((order) => (
                <div key={order.id} className="history-item">
                  <div className="order-meta">
                    <strong>Order #{order.id}</strong>
                    <span>₦{parseFloat(order.total_price || order.total || 0).toLocaleString()}</span>
                  </div>
                  <button className="re-download-btn" onClick={() => window.open(`http://localhost:8001/api/invoices/generate?order_id=${order.id}`, "_blank")}>PDF</button>
                </div>
              ))}
            </div>
            <button className="back-btn" onClick={() => setView("grid")}>Home</button>
          </div>
        ) : isSuccess ? (
          <div className="view-container success-screen">
            <h2>✅ Payment Confirmed!</h2>
            <p>Order ID: #{orderId}</p>
            <button className="back-btn" onClick={() => setIsSuccess(false)}>Continue Shopping</button>
          </div>
        ) : selectedProduct ? (
          // ... inside the selectedProduct ? (...) block
<div className="view-container detail-screen">
  <button className="back-link" onClick={() => setSelectedProduct(null)}>← Back to Products</button>
  <div className="detail-layout">
    {/* MODIFIED IMAGE TAG BELOW */}
    <img 
      src={`http://127.0.0.1:8000/static/${selectedProduct.image_path}`} 
      alt={selectedProduct.name} 
      style={{ 
        maxWidth: "400px",  // Limits the width to a moderate size
        width: "100%",      // Ensures responsiveness on smaller screens
        height: "auto",     // Maintains aspect ratio
        borderRadius: "12px", // Matches your likely card theme
        display: "block",
        margin: "0 auto 20px" // Centers the image and adds spacing
      }}
    />
    <div className="detail-info">
      <h1>{selectedProduct.name}</h1>
      <p className="detail-price">₦{parseFloat(selectedProduct.price).toLocaleString()}</p>
      <button className="add-btn" onClick={() => addToCart(selectedProduct)}>Add to Cart</button>
    </div>
  </div>
</div>
        ) : (
          <div className="product-grid">
            {filteredProducts.map((p) => (
              <div key={p.id} className="product-card">
                <div className="img-frame" onClick={() => setSelectedProduct(p)}>
                  <img src={`http://127.0.0.1:8000/static/${p.image_path}`} alt={p.name} className="zoom-effect" />
                </div>
                <h3>{p.name}</h3>
                <p>₦{parseFloat(p.price).toLocaleString()}</p>
                <button className="add-btn" onClick={() => addToCart(p)}>Add to Cart</button>
              </div>
            ))}
          </div>
        )}
      </main>

      <aside className={`right-sidebar ${cartOpen ? "open" : ""}`}>
        <div className="cart-container">
          <h3>Your Cart</h3>
          <div className="cart-items-list">
  {/* 1. This displays the actual items added to the cart */}
  {cart.map((item, index) => (
    <div key={index} className="cart-item-row">
      <div className="cart-item-info">
        <strong>{item.name}</strong>
        <span>₦{parseFloat(item.price).toLocaleString()}</span>
      </div>
      <button 
        className="remove-item-btn" 
        onClick={() => setCart(cart.filter((_, i) => i !== index))}
      >
        ×
      </button>
    </div>
  ))}

  {/* 2. Show a message if the cart is empty */}
  {cart.length === 0 && <p className="empty-msg">Your shopping bag is empty.</p>}

  {/* 3. Your existing Promo Box (Keep this below the items) */}
  <div className="promo-box-mini">

    <div className="promo-icon">🎁</div>
    <div className="promo-text">
      <strong>Unlock End-of-Year Rewards</strong>
      <span>Register now to get your Order Receipt & track orders live.</span>
    </div>
  </div>
</div>
          <div className="gift-card-input-wrapper">
             <input 
               type="text" 
               placeholder="EOY Gift Code" 
               value={giftCardCode} 
               onChange={(e) => setGiftCardCode(e.target.value)} 
             />
             <button onClick={applyGiftCard}>Apply</button>
          </div>

          <div className="total-section">
            {discount > 0 && <p className="discount-tag">Gift Discount: -₦{discount.toLocaleString()}</p>}
            <p className="final-total">Total: <strong>₦{totalDue.toLocaleString()}</strong></p>
            <button className="vendor-btn paystack" disabled={isProcessing} onClick={checkoutWithPaystack}>
              {isProcessing ? "Processing..." : "Pay with Paystack"}
            </button>
            <button className="clear-cart-btn" onClick={clearCart} disabled={isProcessing || cart.length === 0}>Clear Cart</button>
          </div>
        </div>
      </aside>
    </div>
  );
}

export default App;