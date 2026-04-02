import React, { useEffect, useState } from "react";
import "./App.css";

function App() {
  const [products, setProducts] = useState([]);
  const [category, setCategory] = useState("food"); 
  const [cart, setCart] = useState([]);
  const [cartOpen, setCartOpen] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);

  // 1. Fetch products from Django backend
  useEffect(() => {
    fetch("http://127.0.0.1:8000/api/products/")
      .then((res) => res.json())
      .then((data) => setProducts(data))
      .catch((err) => console.error("Error fetching products:", err));
  }, []);

  // 2. Filter products by category
  const filteredProducts = products.filter((p) => p.category === category);

  const addToCart = (product) => {
    setCart([...cart, product]);
  };

  // 3. TRANSACTION LOGIC: Now with a built-in delay for database consistency
  const checkoutOrder = async () => {
    if (cart.length === 0) return alert("Your cart is empty!");
    
    setIsProcessing(true);

    const calculatedTotal = cart.reduce((sum, item) => sum + parseFloat(item.price || 0), 0);

    try {
      const response = await fetch("http://127.0.0.1:8000/api/orders/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          items: cart.map((item) => ({ 
            id: parseInt(item.id), 
            quantity: 1 
          })),
          total: calculatedTotal.toFixed(2), 
          userId: "001", 
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        console.error("Backend Error Details:", data);
        throw new Error(data.error || "Server validation failed (400)");
      }
      
      // CONFIRMATION
      alert(`✅ Payment Received!\nOrder ID: ${data.id}\nClick OK to generate your receipt.`);

      // FIX: Wait 1.5 seconds before calling FastAPI
      // This prevents the 404 "Order not found" race condition
      setTimeout(() => {
        window.open(`http://localhost:8001/api/invoices/generate?order_id=${data.id}`, "_blank");
      }, 1500);

      setCart([]);
      setCartOpen(false);
    } catch (err) {
      console.error("Checkout Error:", err);
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
        <button className="cart-toggle" onClick={() => setCartOpen(!cartOpen)}>
          🛒 Cart ({cart.length})
        </button>
      </header>

      <nav className="main-nav">
        <ul>
          <li><a href="#">Home</a></li>
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
              onClick={() => setCategory(cat.id)}
            >
              {cat.label}
            </button>
          ))}
        </nav>
      </aside>

      <main>
        <h2>{category.toUpperCase()} SECTION</h2>
        <div className="product-grid">
          {filteredProducts.map((p) => (
            <div key={p.id} className="product-card">
              <img
                src={`http://127.0.0.1:8000/static/${p.image_path}`}
                alt={p.name}
                style={{ width: '100%', height: '200px', objectFit: 'cover' }}
                onError={(e) => { e.target.src = "https://via.placeholder.com/150"; }} 
              />
              <h3>{p.name}</h3>
              <p>₦{parseFloat(p.price).toLocaleString()}</p>
              <button className="add-btn" onClick={() => addToCart(p)}>
                Add to Cart
              </button>
            </div>
          ))}
          {filteredProducts.length === 0 && <p>No items in this category yet.</p>}
        </div>
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
            <button 
              className="vendor-btn paystack" 
              disabled={isProcessing} 
              onClick={checkoutOrder}
            >
              {isProcessing ? "Processing..." : "Paystack"}
            </button>
          </div>
        </div>
      </aside>

      <footer><p>System Status: Operational | v1.0.8</p></footer>
    </div>
  );
}

export default App;