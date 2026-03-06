const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({ headless: "new", args: ['--no-sandbox'] });
  const page = await browser.newPage();
  
  page.on('console', msg => console.log('PAGE LOG:', msg.text()));
  page.on('pageerror', error => console.log('PAGE ERROR:', error.message));
  page.on('requestfailed', request => console.log('REQUEST FAILED:', request.url(), request.failure().errorText));

  console.log("Navigating to http://localhost:3000");
  await page.goto('http://localhost:3000', { waitUntil: 'networkidle0' });
  
  const jobsText = await page.evaluate(() => document.querySelector('.count')?.textContent);
  console.log("Jobs count text:", jobsText);
  
  await browser.close();
})();
