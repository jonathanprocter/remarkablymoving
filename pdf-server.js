// pdf-server.js - Node.js server for PDF generation
const express = require('express');
const cors = require('cors');
const path = require('path');

// Import the PDF generator backend code
const pdfRoutes = require('./pdf-generator-backend');

const app = express();

// Middleware
app.use(cors());
app.use(express.json({ limit: '50mb' }));
app.use(express.static('public'));

// Use PDF generation routes
app.use('/api', pdfRoutes);

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'ok', service: 'pdf-generator' });
});

const PORT = process.env.PDF_SERVER_PORT || 3001;
app.listen(PORT, '0.0.0.0', () => {
  console.log(`PDF Generation Server running on port ${PORT}`);
  console.log(`Health check: http://localhost:${PORT}/health`);
  console.log(`PDF endpoint: http://localhost:${PORT}/api/generate-planner-pdf`);
});