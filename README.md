# Laptop Outlet Monitor 💻🚀

An automated web scraping system that monitors **Lenovo Certified Refurbished/Outlet** and **ASUS Outlet** stores in India. It detects new listings and stock additions, notifying you instantly via push notifications on your phone or computer, **even when your laptop is completely powered off**.

## How It Works

1. **Automation:** A **GitHub Actions** cron job runs on GitHub's cloud servers every hour.
2. **Scraping:** It spins up a headless browser to load the dynamic Lenovo page, parses it alongside the ASUS page, and compares the listings with the last-known state (`products_db.json`).
3. **Alerts:** If a new product is added or goes back in stock, it sends a push notification to your phone/browser using **ntfy.sh**.
4. **State Storage:** The script updates `products_db.json` and pushes the updated database back to your GitHub repository automatically.

---

## Setup Instructions

Follow these simple steps to activate your monitor:

### Step 1: Subscribe to Push Notifications

1. **On your Phone (Android/iOS):**
   - Download the free **ntfy** app from Google Play or the iOS App Store.
   - Open the app, tap the **`+`** icon, and subscribe to a unique topic of your choice (e.g. `my_secret_laptop_deals_2026`).
2. **On your Browser (Alternative):**
   - Go to `https://ntfy.sh/my_secret_laptop_deals_2026` (replace with your secret topic).
   - Click **Subscribe** to enable desktop push alerts.

### Step 2: Create a Private GitHub Repository

1. Go to [GitHub](https://github.com) and log in.
2. Click **New** to create a repository.
3. Make it **Private** (recommended, since it stores your listings and configuration).
4. Set the repository name (e.g., `laptop-monitor`).
5. **Do not** add a README, license, or gitignore file (leave them unchecked).

### Step 3: Push This Code to GitHub

Open terminal/PowerShell, navigate to your project directory (`c:\Users\dubey\Desktop\Project_to_buy_laptop`), and run:

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/YOUR_REPO_NAME.git
git push -u origin main
```

*(Replace `YOUR_GITHUB_USERNAME` and `YOUR_REPO_NAME` with your actual GitHub username and repository name).*

### Step 4: Configure Your Secret Topic (Optional but Recommended)

By default, the script alerts to the topic `dubey_laptop_alerts_2026`. To set it to your personal secret topic:

1. In your GitHub repository, go to **Settings** > **Secrets and variables** > **Actions**.
2. Click **New repository secret**.
3. Set the **Name** to `NTFY_TOPIC`.
4. Set the **Value** to your secret topic name (e.g., `my_secret_laptop_deals_2026`).
5. Click **Add secret**.

### Step 5: Enable Write Permissions for the Bot

To allow the workflow to commit the updated database back to git:

1. In your GitHub repository, go to **Settings** > **Actions** > **General**.
2. Scroll down to **Workflow permissions**.
3. Select **Read and write permissions**.
4. Click **Save**.

---

## Testing the Monitor

You can trigger a manual run to test the notifications:

1. Go to the **Actions** tab in your GitHub repository.
2. Select **Laptop Outlet Monitor** on the left.
3. Click **Run workflow** > **Run workflow**.
4. Within 2 minutes, you will receive a push notification listing all current outlet items (since the database starts empty, all listings are treated as new!). Future runs will only notify you when *new* items appear or existing ones go back in stock.
