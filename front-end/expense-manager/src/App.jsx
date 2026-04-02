import React, { useEffect, useState } from "react";
import "./App.css";

function App() {
  const [products, setProducts] = useState([]);
  const [category, setCategory] = useState("food");
  const [cart, setCart] = useState([]);
  const [cartOpen, setCartOpen] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);

  const [searchTerm, setSearchTerm] = useState("");
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [isSuccess, setIsSuccess] = useState(false);
  const [orderId, setOrderId] = useState("");

  useEffect(() => {
    fetch("http://127.0.0.1:8000/api/products/")
      .then((res) => res.json())
      .then((data) => setProducts(data))
      .catch((err) => console.error("Error fetching products:", err));
  }, []);

  const filteredProducts = products.filter((p) => {
    const matchesCategory = p.category === category;
    const matchesSearch = p.name.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  const addToCart = (product) => {
    setCart([...cart, product]);
  };

  // NEW: Clear Cart Logic
  const clearCart = () => {
    if (cart.length === 0) return;
    if (window.confirm("Are you sure you want to empty your cart?")) {
      setCart([]);
    }
  };

  const checkoutOrder = async () => {
    if (cart.length === 0) return alert("Your cart is empty!");
    setIsProcessing(true);

    const calculatedTotal = cart.reduce((sum, item) => sum + parseFloat(item.price || 0), 0);

    try {
      const response = await fetch("http://127.0.0.1:8000/api/orders/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          items: cart.map((item) => ({ id: parseInt(item.id), quantity: 1 })),
          total: calculatedTotal.toFixed(2),
          userId: "001",
        }),
      });

      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Server validation failed");

      setOrderId(data.id);
      setIsSuccess(true);
      setCart([]);
      setCartOpen(false);

      setTimeout(() => {
        window.open(`http://localhost:8001/api/invoices/generate?order_id=${data.id}`, "_blank");
      }, 1500);

    } catch (err) {
      alert(`Checkout failed: ${err.message}`);
    } finally {
      setIsProcessing(false);
    }
  };

  const totalDue = cart.reduce((sum, item) => sum + parseFloat(item.price || 0), 0);

  return (
    <div className="app-grid-wrapper">
      <header>
        <h1>Lagos Tech Hub</h1>
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
          <li><a href="#" onClick={() => {setIsSuccess(false); setSelectedProduct(null)}}>Home</a></li>
          <li><a href="#">Shop</a></li>
          <li><a href="#">Account</a></li>
        </ul>
      </nav>

      <aside className="left-sidebar">
        <h3>Categories</h3>
        <nav className="side-nav">
          {[
            { id: "food", label: "Food & Drinks" },
            { id: "electronics", label: "Electronics" },
            { id: "office", label: "Office Supplies" },
            { id: "clothing", label: "Clothing" },
            { id: "automotive", label: "Automotive" },
          ].map((cat) => (
            <button 
              key={cat.id}
              className={category === cat.id ? "active" : ""} 
              onClick={() => {
                setCategory(cat.id);
                setSearchTerm("");
                setSelectedProduct(null);
                setIsSuccess(false);
              }}
            >
              {cat.label}
            </button>
          ))}
        </nav>
      </aside>

      <main>
        {isSuccess ? (
          <div className="view-container success-screen">
            <h2>✅ Order Confirmed!</h2>
            <p>Your Order ID is: <strong>#{orderId}</strong></p>
            <p>Your receipt is generating in a new tab...</p>
            <button className="back-btn" onClick={() => setIsSuccess(false)}>Continue Shopping</button>
          </div>
        ) : selectedProduct ? (
          <div className="view-container detail-screen">
            <button className="back-link" onClick={() => setSelectedProduct(null)}>← Back to Grid</button>
            <div className="detail-layout">
              <img src={`http://127.0.0.1:8000/static/${selectedProduct.image_path}`} alt={selectedProduct.name} />
              <div className="detail-info">
                <h1>{selectedProduct.name}</h1>
                <p className="detail-price">₦{parseFloat(selectedProduct.price).toLocaleString()}</p>
                <p>Category: {selectedProduct.category}</p>
                <button className="add-btn" onClick={() => addToCart(selectedProduct)}>Add to Cart</button>
              </div>
            </div>
          </div>
        ) : (
        <>
          <h2>{category.toUpperCase()} SECTION</h2>
          <div className="product-grid">
            {filteredProducts.map((p) => (
              <div key={p.id} className="product-card">
                <div className="img-frame" onClick={() => setSelectedProduct(p)}>
                  <img
                    src={`http://127.0.0.1:8000/static/${p.image_path}`}
                    alt={p.name}
                    className="zoom-effect"
                    onError={(e) => { e.target.src = "https://via.placeholder.com/150"; }} 
                  />
                  <div className="img-overlay">Click to Expand</div>
                </div>
                <h3>{p.name}</h3>
                <p>₦{parseFloat(p.price).toLocaleString()}</p>
                <button className="add-btn" onClick={() => addToCart(p)}>
                  Add to Cart
                </button>
              </div>
            ))}
            {filteredProducts.length === 0 && <p>No items found.</p>}
          </div>
        </>
        )}
      </main>

      <aside className={`right-sidebar ${cartOpen ? "open" : ""}`}>
        <div className="cart-container">
          <h3>Your Selection</h3>
          <div className="cart-items-list">
            {cart.length === 0 ? <p>Cart is empty</p> : cart.map((item, index) => (
              <div key={index} className="cart-item">
                <span>{item.name}</span>
                <span>₦{parseFloat(item.price).toLocaleString()}</span>
              </div>
            ))}
          </div>
          <div className="total-section">
            <h4>Total Due:</h4>
            <p className="total-amount">₦{totalDue.toLocaleString()}</p>
          </div>
          <hr />
          <h4>Checkout via:</h4>
          <div className="payment-vendors">
            <button className="vendor-btn paystack" disabled={isProcessing} onClick={checkoutOrder}>
              {isProcessing ? "Processing..." : "Paystack"}
            </button>
            
            {/* NEW: Clear Cart Button positioned under Paystack */}
            <button 
              className="clear-cart-btn" 
              onClick={clearCart} 
              disabled={isProcessing || cart.length === 0}
            >
              Clear Cart
            </button>
          </div>
        </div>
      </aside>

      <footer><p>System Status: Operational | v1.1.0</p></footer>
    </div>
  );
}

export default App;