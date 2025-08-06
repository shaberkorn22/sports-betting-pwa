const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');
const { Pool } = require('pg');
require('dotenv').config();

const app = express();
app.use(cors());
app.use(bodyParser.json());

// Initialize PostgreSQL pool
const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  // Enable SSL in production
  ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false,
});

// Get daily picks
app.get('/api/picks', async (req, res) => {
  try {
    const result = await pool.query('SELECT * FROM picks ORDER BY confidence DESC LIMIT 20');
    res.json(result.rows);
  } catch (err) {
    console.error('Error fetching picks:', err);
    res.status(500).json({ error: 'Failed to fetch picks' });
  }
});

// Submit feedback (like/dislike/tail)
app.post('/api/feedback', async (req, res) => {
  const { pick_id, feedback_type } = req.body;
  if (!pick_id || !feedback_type) {
    return res.status(400).json({ error: 'pick_id and feedback_type are required' });
  }
  try {
    await pool.query('INSERT INTO feedback (pick_id, feedback_type) VALUES ($1, $2)', [pick_id, feedback_type]);
    res.json({ message: 'Feedback recorded' });
  } catch (err) {
    console.error('Error recording feedback:', err);
    res.status(500).json({ error: 'Failed to record feedback' });
  }
});

// Root route
app.get('/', (req, res) => {
  res.send('Backend API is running');
});

const PORT = process.env.PORT || 3001;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
