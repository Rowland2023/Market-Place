// Example React API configuration
const API_BASE_URL = "http://localhost:8001/api";

export const fetchInvoices = async () => {
  const response = await fetch(`${API_BASE_URL}/invoices`);
  return response.json();
};