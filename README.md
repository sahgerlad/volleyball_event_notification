# NYC Volleyball Event Notification

Scrapes volleyball event listings from [Big City Volleyball](https://app.bigcityvolleyball.com), [NY Urban](https://www.nyurban.com), and optionally [Volo volleyball events](https://www.volosports.com/discover?cityName=New%20York%20Metro%20Area&subView=LEAGUE&view=SPORTS&sportNames%5B0%5D=Volleyball) on an hourly schedule via GitHub Actions. Sends an email notification when new events become available.

## Setup

### 1. Fork this repository

### 2. Create a Gmail App Password

The scraper sends notifications from a Gmail account. It's recommended to create a dedicated Gmail account for this rather than using your personal one. You'll need a [Google App Password](https://support.google.com/accounts/answer/185833):

1. Go to your Google Account > Security > 2-Step Verification (must be enabled)
2. At the bottom, select **App passwords**
3. Create a new app password and copy it

### 3. Configure GitHub Secrets

Go to your fork's **Settings > Secrets and variables > Actions** and add:

| Secret              | Description                                   |
| ------------------- | --------------------------------------------- |
| `EMAIL_RECIPIENT` | The email address that receives notifications |
| `APP_PASSWORD`    | The Gmail App Password from step 2            |

### 4. Update the sender email

In `src/config.py`, change `EMAIL_SENDER` to the Gmail address that owns the App Password:

```python
EMAIL_SENDER = "your-email@gmail.com"
```

### 5. Enable the workflow

Go to **Actions** in your fork, select the **Volleyball Event Scraper** workflow, and click **Enable workflow**. It runs hourly and can also be triggered manually via **Run workflow**.

## Enabling Volo (Optional)

The [Volo Sports](https://www.volosports.com) scraper is disabled by default. The scraper works in two modes depending on whether you provide login credentials:

- **Without credentials:** Discovers new pickup volleyball events and sends notifications, but cannot see event capacity or auto-register.
- **With credentials:** Logs into your Volo account, filters out full events by checking capacity, and automatically registers you for **free events**. To avoid cancellation fees, auto-registration only applies to events more than 24 hours away (configurable via `SIGNUP_NOTICE` in `src/scrapers/volo/volo_config.py`).

To enable it:

**1. Add a GitHub Actions variable:**

Go to **Settings > Secrets and variables > Actions > Variables** and add:

| Variable        | Value    |
| --------------- | -------- |
| `ENABLE_VOLO` | `true` |

**2. Add GitHub Secrets (optional):**

These are only needed if you want capacity filtering and auto-registration. The scraper will still discover and notify about events without them.

| Secret            | Description                       |
| ----------------- | --------------------------------- |
| `VOLO_USERNAME` | Your Volo Sports account email    |
| `VOLO_PASSWORD` | Your Volo Sports account password |

**3. Customize venue filter (optional):**

The `URL_QUERY` in `src/scrapers/volo/volo_config.py` is pre-configured to filter for pickup volleyball at specific venues. To change this, go [here](https://www.volosports.com/discover?cityName=New%20York%20Metro%20Area&subView=LEAGUE&view=SPORTS&sportNames%5B0%5D=Volleyball), apply your preferred filters, then copy the resulting URL and replace `URL_QUERY`.
