import React from 'react';
// No need to import App.css here if it's already imported in App.jsx!
import '../App.css';             

function HelloWorld() {
  return (
    <div className="ledger-card">
      <h1 className="ledger-title">Hello, World!</h1>
      <p className="ledger-status">SYSTEM_STATUS: OPERATIONAL</p>
    </div>
  );
}

export default HelloWorld;