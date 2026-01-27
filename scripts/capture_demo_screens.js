const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

// Configuration
const BASE_URL = 'http://localhost:3000';
const ASSETS_DIR = path.resolve(__dirname, '../docs/assets');

// Ensure assets directory exists
if (!fs.existsSync(ASSETS_DIR)) {
  fs.mkdirSync(ASSETS_DIR, { recursive: true });
}

(async () => {
    console.log('🚀 Starting Demo Screenshot Capture (Mocked Mode)...');
    const browser = await chromium.launch({ headless: false, slowMo: 300 });
    const context = await browser.newContext({
        viewport: { width: 1280, height: 720 },
        recordVideo: { dir: path.resolve(ASSETS_DIR, 'videos') }
    });
    const page = await context.newPage();

    // --- MOCKS ---
    // Mock Signup
    await page.route('**/api/v1/auth/signup', route => {
        console.log('Intercepted Login/Signup');
        route.fulfill({ 
            status: 200, 
            contentType: 'application/json',
            body: JSON.stringify({ success: true, token: 'mock_token' }) 
        });
    });

    // Mock Evaluation (Dynamic based on answer?)
    await page.route('**/api/v1/evaluation/evaluate', async route => {
        const postData = JSON.parse(route.request().postData());
        console.log('Intercepted Evaluation:', postData.learner_response);
        
        let response;
        if (postData.learner_response.includes('filters') || postData.learner_response.includes('SELECT')) {
            // Correct
            response = {
                success: true,
                score: 0.9,
                error_type: "CORRECT",
                feedback: "Excellent! That is correct.",
                decision: "PROCEED",
                new_mastery: 0.9,
                misconception: null
            };
        } else {
            // Wrong (The Gap)
            response = {
                success: true,
                score: 0.3,
                error_type: "CONCEPTUAL",
                feedback: "Not quite. INNER JOIN requires matching keys in BOTH tables.",
                decision: "REMEDIATE",
                new_mastery: 0.3,
                misconception: "Confusing JOIN with UNION"
            };
        }
        
        // Add random delay to simulate AI thinking
        await new Promise(r => setTimeout(r, 1000));
        route.fulfill({ 
            status: 200, 
            contentType: 'application/json',
            body: JSON.stringify(response) 
        });
    });

    // Mock Tutor
    await page.route('**/api/v1/tutoring/ask', async route => {
        console.log('Intercepted Tutor Ask');
        await new Promise(r => setTimeout(r, 1500));
        route.fulfill({ 
            status: 200, 
            contentType: 'application/json',
            body: JSON.stringify({
                success: true,
                guidance: "That's a good start! But remember, INNER JOIN is strict. It only keeps rows that have partners in both tables.",
                question: "If Table A has 5 rows and Table B has 5 rows, but no IDs match, how many rows will the result have?",
                hint_level: 2,
                difficulty: 3,
                concept_id: "SQL_INNER_JOIN"
            }) 
        });
    });

    // Mock Tutor Principles (called by hook?)
    await page.route('**/api/v1/tutoring/principles', route => 
        route.fulfill({ status: 200, body: JSON.stringify([]) })
    );


    // Helper to save screenshot
    const saveScreenshot = async (name) => {
        const filepath = path.join(ASSETS_DIR, name);
        await page.screenshot({ path: filepath, fullPage: true });
        console.log(`📸 Saved: ${name}`);
    };

    try {
        // --- PHASE 1: SIGNUP ---
        console.log('--- Phase 1: Registration ---');
        await page.goto(`${BASE_URL}/auth/signup`, { timeout: 90000 });
        await page.waitForLoadState('networkidle');
        await saveScreenshot('demo_01_signup_empty.png');
        await saveScreenshot('demo_02_signup_filled.png');
        await saveScreenshot('demo_03_dashboard_initial.png');
        await saveScreenshot('demo_04_quiz_start.png');
        await saveScreenshot('demo_05_quiz_results_gap.png');
        await saveScreenshot('demo_07_tutor_start.png');
        await saveScreenshot('demo_08_tutor_feedback.png');

        console.log('✅ Demo Capture Complete');

    } catch (error) {
        console.error('❌ Error during capture:', error);
        await page.screenshot({ path: path.join(ASSETS_DIR, 'error_state.png') });
    } finally {
        await browser.close();
    }
})();
