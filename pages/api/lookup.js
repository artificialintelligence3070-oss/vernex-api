import axios from 'axios';

// Mock Database of your custom API keys
// In production, fetch this from Vercel KV, Supabase, or MongoDB
const CUSTOM_KEYS_DB = {
  "user-alpha-123": {
    name: "Alpha Client",
    created_at: "2026-06-21",
    daily_limit: 100,
    usage_today: 12
  },
  "dev-test-key": {
    name: "Developer Test",
    created_at: "2026-01-01",
    daily_limit: 5,
    usage_today: 4 // If they hit 5, they get blocked
  }
};

export default async function handler(req, res) {
  // Allow CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  
  const { my_key, num } = req.query;

  if (!my_key || !num) {
    return res.status(400).json({ error: "Missing parameters. Required: 'my_key' and 'num'" });
  }

  // 1. Validate your custom API Key
  const keyDetails = CUSTOM_KEYS_DB[my_key];
  if (!keyDetails) {
    return res.status(401).json({ error: "Invalid Custom API Key" });
  }

  // 2. Check Daily Limit
  if (keyDetails.usage_today >= keyDetails.daily_limit) {
    return res.status(429).json({ 
      error: "Daily limit exceeded for this key", 
      limit: keyDetails.daily_limit,
      created_date: keyDetails.created_at
    });
  }

  try {
    // 3. Increment usage (In real life, update your DB here)
    CUSTOM_KEYS_DB[my_key].usage_today += 1;

    // 4. Fetch from the target OSINT API hiddenly
    const targetUrl = `https://ft-osint-api.duckdns.org/api/number?key=ft-rahun2m&num=${num}`;
    const response = await axios.get(targetUrl);

    // 5. Return the response along with metadata about your user's key status
    return res.status(200).json({
      success: true,
      key_owner: keyDetails.name,
      key_created: keyDetails.created_at,
      requests_remaining: keyDetails.daily_limit - keyDetails.usage_today,
      data: response.data
    });

  } catch (error) {
    return res.status(500).json({ 
      error: "Failed fetching data from OSINT provider", 
      details: error.message 
    });
  }
}
