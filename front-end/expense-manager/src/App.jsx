import React, { useEffect, useState } from "react";
import "./App.css";

function App() {
  const [products, setProducts] = useState([]);
  const [category, setCategory] = useState("food"); // Matches your PitBull Rice category
  const [cart, setCart] = useState([]);
  const [cartOpen, setCartOpen] = useState(false);

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

  const checkoutOrder = async () => {
    try {
      const response = await fetch("http://127.0.0.1:8000/api/orders/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          items: cart.map((item) => ({ id: item.id, quantity: 1 })),
          total: cart.reduce((sum, item) => sum + parseFloat(item.price), 0),
          userId: "demo-user",
        }),
      });
      const data = await response.json();
      alert(`Order placed successfully! Order ID: ${data.id}`);
      setCart([]);
    } catch (err) {
      console.error(err);
      alert("Checkout failed. Please try again.");
    }
  };

  const totalDue = cart.reduce((sum, item) => sum + parseFloat(item.price), 0);

  return (
    <div className="app-grid-wrapper">
      <header>
        <h1>Market Place</h1>
        <button className="cart-toggle" onClick={() => setCartOpen(!cartOpen)}>
          🛒 Cart ({cart.length})
        </button>
      </header>

      <nav className="main-nav">
        <ul>
          <li><a href="#">Home</a></li>
          <li><a href="#">Shop</a></li>
          <li><a href="#">Deals</a></li>
          <li><a href="#">Support</a></li>
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
            { id: "books", label: "Books & Media" },
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
        <h2>{category.toUpperCase()} Marketplace</h2>
        <div className="product-grid">
          {filteredProducts.map((p) => (
            <div key={p.id} className="product-card">
              {/* Updated Image Logic: Using the verified 127.0.0.1 address */}
              <img
                src={`http://127.0.0.1:8000/static/${p.image_path}`}
                alt={p.name}
                style={{ width: '100%', height: '200px', objectFit: 'cover' }}
                onError={(e) => { 
                  console.error("React could not load image at:", e.target.src);
                  e.target.src = "https://via.placeholder.com/150"; 
                }} 
              />
              <h3>{p.name}</h3>
              <p>₦{parseFloat(p.price).toLocaleString()}</p>
              <button className="add-btn" onClick={() => addToCart(p)}>
                Add to Cart
              </button>
            </div>
          ))}
          {filteredProducts.length === 0 && (
            <p className="no-products">No products found in the {category} category.</p>
          )}
        </div>
      </main>

      <aside className={`right-sidebar ${cartOpen ? "open" : ""}`}>
        <div className="cart-container">
          <h3>Your Selection</h3>
          <div className="cart-items-list">
            {cart.length === 0 ? (
              <p>Cart is empty</p>
            ) : (
              cart.map((item, index) => (
                <div key={index} className="cart-item">
                  <span>{item.name}</span>
                  <span>₦{parseFloat(item.price).toLocaleString()}</span>
                </div>
              ))
            )}
          </div>
          <div className="total-section">
            <h4>Total Due:</h4>
            <p className="total-amount">₦{totalDue.toLocaleString()}</p>
          </div>
          <hr />
          <h4>Checkout via:</h4>
          <div className="payment-vendors">
            <button className="vendor-btn paystack" onClick={checkoutOrder}>Paystack</button>
            <button className="vendor-btn flutterwave" onClick={checkoutOrder}>Flutterwave</button>
          </div>
          {cart.length > 0 && (
            <button className="clear-btn" onClick={() => setCart([])}>
              Clear Cart
            </button>
          )}
        </div>
      </aside>

      <footer><p>v1.0.4 - Operational</p></footer>
    </div>
  );
}

export default App;