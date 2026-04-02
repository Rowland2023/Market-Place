import React, { useState, useEffect } from 'react';
import axios from 'axios';

const ProductStore = () => {
    const [products, setProducts] = useState([]);

    useEffect(() => {
        // We call the Django API
        axios.get('http://localhost:8000/api/products/')
            .then(res => {
                setProducts(res.data);
            })
            .catch(err => console.log("Frontend Error:", err));
    }, []);

    return (
        <div className="product-grid">
            {products.map(product => (
                <div key={product.id} className="product-card">
                    <h3>{product.name}</h3>
                    <p>₦{product.price}</p>
                    <button>Add to Cart</button>
                </div>
            ))}
        </div>
    );
};