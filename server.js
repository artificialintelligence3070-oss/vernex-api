const express = require('express');
const axios = require('axios');
const fs = require('fs-extra');
const { v4: uuidv4 } = require('uuid');

const app = express();
const PORT = 3000;

app.use(express.json());

const DB_FILE = './keys.json';

// Create DB if not exists
if (!fs.existsSync(DB_FILE)) {
    fs.writeJsonSync(DB_FILE, []);
}

// Load Keys
function loadKeys() {
    return fs.readJsonSync(DB_FILE);
}

// Save Keys
function saveKeys(keys) {
    fs.writeJsonSync(DB_FILE, keys, { spaces: 2 });
}

// Remove expired keys automatically
function cleanExpiredKeys() {
    const keys = loadKeys();
    const now = Date.now();

    const validKeys = keys.filter(k => k.expiry > now);

    saveKeys(validKeys);
}

// Run cleanup every 1 minute
setInterval(cleanExpiredKeys, 60000);

// Validate API Key
function validateKey(apiKey) {
    cleanExpiredKeys();

    const keys = loadKeys();
    const found = keys.find(k => k.key === apiKey);

    if (!found) {
        return {
            valid: false,
            message: 'Invalid or Expired API Key'
        };
    }

    return {
        valid: true,
        data: found
    };
}

// Generate API Key
app.get('/generate-key', (req, res) => {
    const duration = req.query.duration || '1d';

    let ms = 86400000;

    if (duration.endsWith('d')) {
        ms = parseInt(duration) * 86400000;
    } else if (duration.endsWith('h')) {
        ms = parseInt(duration) * 3600000;
    } else if (duration.endsWith('m')) {
        ms = parseInt(duration) * 60000;
    }

    const apiKey = 'vernex-' + uuidv4().replace(/-/g, '').slice(0, 24);

    const expiry = Date.now() + ms;

    const keys = loadKeys();

    keys.push({
        key: apiKey,
        expiry
    });

    saveKeys(keys);

    res.json({
        status: true,
        api_key: apiKey,
        expires_at: new Date(expiry).toISOString(),
        owner: 'VERNEX'
    });
});

// Main Number API
app.get('/api/number', async (req, res) => {
    try {
        const apiKey = req.query.key;
        const num = req.query.num;

        if (!apiKey) {
            return res.json({
                status: false,
                message: 'API key required'
            });
        }

        if (!num) {
            return res.json({
                status: false,
                message: 'Number required'
            });
        }

        // Validate Key
        const keyCheck = validateKey(apiKey);

        if (!keyCheck.valid) {
            return res.json({
                status: false,
                message: keyCheck.message
            });
        }

        // External API Request
        const response = await axios.get(
            `https://ft-osint-api.duckdns.org/api/number?key=ft-rahun2m&num=${num}`
        );

        const data = response.data;

        // Remove unwanted fields
        delete data.by;
        delete data.channel;

        // Add your branding
        data.api_by = 'VERNEX';

        return res.json(data);

    } catch (error) {
        return res.json({
            status: false,
            message: 'Failed to fetch data',
            error: error.message,
            api_by: 'VERNEX'
        });
    }
});

// Key List
app.get('/keys', (req, res) => {
    cleanExpiredKeys();

    const keys = loadKeys();

    res.json({
        total_keys: keys.length,
        keys
    });
});

// Delete Key
app.get('/delete-key', (req, res) => {
    const key = req.query.key;

    if (!key) {
        return res.json({
            status: false,
            message: 'Key required'
        });
    }

    const keys = loadKeys();

    const filtered = keys.filter(k => k.key !== key);

    saveKeys(filtered);

    res.json({
        status: true,
        message: 'Key deleted successfully'
    });
});

app.listen(PORT, () => {
    console.log(`VERNEX API running on port ${PORT}`);
});
