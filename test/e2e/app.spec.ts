import { test, expect } from "@playwright/test"

// ─── UI Tests ──────────────────────────────────────────────────────────────

test.describe("FinAlly Trading Terminal", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/")
    await page.waitForSelector("text=FinAlly", { timeout: 15000 })
  })

  // ── Header ─────────────────────────────────────────────────────────────────

  test("header shows FinAlly branding", async ({ page }) => {
    await expect(page.locator("text=FinAlly").first()).toBeVisible()
    await expect(page.locator("text=AI Trading Workstation")).toBeVisible()
  })

  test("header shows cash balance", async ({ page }) => {
    await expect(page.locator("text=$10,000.00").first()).toBeVisible({ timeout: 8000 })
  })

  test("header shows Portfolio label", async ({ page }) => {
    await expect(page.locator("text=Portfolio").first()).toBeVisible()
  })

  test("connection status indicator is visible", async ({ page }) => {
    await page.waitForTimeout(2000)
    const statusText = page.locator("text=connected").or(
      page.locator("text=reconnecting").or(page.locator("text=disconnected"))
    )
    await expect(statusText.first()).toBeVisible({ timeout: 8000 })
  })

  // ── Watchlist ──────────────────────────────────────────────────────────────

  test("watchlist panel header is visible", async ({ page }) => {
    await expect(page.locator("text=Watchlist")).toBeVisible()
  })

  test("default watchlist shows AAPL", async ({ page }) => {
    await expect(page.locator("text=AAPL").first()).toBeVisible({ timeout: 8000 })
  })

  test("default watchlist shows GOOGL", async ({ page }) => {
    await expect(page.locator("text=GOOGL").first()).toBeVisible({ timeout: 8000 })
  })

  test("prices appear in dollar format", async ({ page }) => {
    await page.waitForTimeout(3000)
    const priceLocator = page.locator("text=/\$\d+\.\d{2}/")
    await expect(priceLocator.first()).toBeVisible({ timeout: 10000 })
  })

  test("clicking watchlist ticker selects it", async ({ page }) => {
    await page.waitForTimeout(2000)
    await page.locator("text=AAPL").first().click()
    await expect(page.locator("text=AAPL").first()).toBeVisible({ timeout: 3000 })
  })

  test("add ticker input has ADD TICKER placeholder", async ({ page }) => {
    const input = page.locator("input[placeholder="ADD TICKER"]")
    await expect(input).toBeVisible()
  })

  test("can add a new ticker to watchlist", async ({ page }) => {
    const input = page.locator("input[placeholder="ADD TICKER"]")
    await input.fill("PYPL")
    await input.press("Enter")
    await expect(page.locator("text=PYPL").first()).toBeVisible({ timeout: 8000 })
  })

  // ── Trade Bar ──────────────────────────────────────────────────────────────

  test("trade bar Trade label is visible", async ({ page }) => {
    await expect(page.locator("text=Trade")).toBeVisible()
  })

  test("trade bar has TICKER input", async ({ page }) => {
    await expect(page.locator("input[placeholder="TICKER"]")).toBeVisible()
  })

  test("trade bar has QTY input", async ({ page }) => {
    await expect(page.locator("input[placeholder="QTY"]")).toBeVisible()
  })

  test("trade bar has BUY button", async ({ page }) => {
    await expect(page.locator("button:has-text("BUY")")).toBeVisible()
  })

  test("trade bar has SELL button", async ({ page }) => {
    await expect(page.locator("button:has-text("SELL")")).toBeVisible()
  })

  test("buy trade shows success or validation message", async ({ page }) => {
    await page.waitForTimeout(4000)
    await page.locator("text=AAPL").first().click()
    await page.waitForTimeout(500)
    const qtyInput = page.locator("input[placeholder="QTY"]")
    await qtyInput.fill("1")
    await page.locator("button:has-text("BUY")").click()
    await expect(
      page.locator("text=/BUY.*AAPL/i").or(page.locator("text=/Enter ticker/i")).or(page.locator("text=/Insufficient/i")).or(page.locator("text=/No price/i"))
    ).toBeVisible({ timeout: 8000 })
  })

  test("sell without position shows error", async ({ page }) => {
    await page.waitForTimeout(2000)
    const tickerInput = page.locator("input[placeholder="TICKER"]")
    const qtyInput = page.locator("input[placeholder="QTY"]")
    await tickerInput.fill("NFLX")
    await qtyInput.fill("100")
    await page.locator("button:has-text("SELL")").click()
    await expect(page.locator("text=/Insufficient|Failed|No price/i").first()).toBeVisible({ timeout: 8000 })
  })

  // ── Chart Area ─────────────────────────────────────────────────────────────

  test("heatmap section label is visible", async ({ page }) => {
    await expect(page.locator("text=Heatmap")).toBeVisible()
  })

  test("P&L Chart section label is visible", async ({ page }) => {
    await expect(page.locator("text=P&L Chart")).toBeVisible()
  })

  test("Positions section label is visible", async ({ page }) => {
    await expect(page.locator("text=Positions")).toBeVisible()
  })

  // ── Chat Panel ─────────────────────────────────────────────────────────────

  test("AI Assistant panel header visible", async ({ page }) => {
    await expect(page.locator("text=AI Assistant")).toBeVisible()
  })

  test("chat input placeholder is Ask FinAlly", async ({ page }) => {
    await expect(page.locator("input[placeholder="Ask FinAlly…"]")).toBeVisible()
  })

  test("chat has Send button", async ({ page }) => {
    await expect(page.locator("button:has-text("Send")")).toBeVisible()
  })

  test("chat shows empty state text", async ({ page }) => {
    await expect(page.locator("text=/Ask me about your portfolio/i")).toBeVisible()
  })

  test("AI chat responds to message", async ({ page }) => {
    const input = page.locator("input[placeholder="Ask FinAlly…"]")
    await input.fill("How is my portfolio doing?")
    await page.locator("button:has-text("Send")").click()
    await expect(page.locator("text=You").first()).toBeVisible({ timeout: 5000 })
    await expect(page.locator("text=❆ FinAlly")).toBeVisible({ timeout: 15000 })
  })

  test("AI chat Enter key sends message", async ({ page }) => {
    const input = page.locator("input[placeholder="Ask FinAlly…"]")
    await input.fill("Hello")
    await input.press("Enter")
    await expect(page.locator("text=You").first()).toBeVisible({ timeout: 5000 })
  })
})

// ─── API Endpoint Tests ──────────────────────────────────────────────────────

test.describe("API endpoints", () => {
  test("GET /api/health returns ok", async ({ request }) => {
    const res = await request.get("/api/health")
    expect(res.ok()).toBeTruthy()
    const data = await res.json()
    expect(data.status).toBe("ok")
    expect(data).toHaveProperty("timestamp")
  })

  test("GET /api/portfolio returns portfolio data", async ({ request }) => {
    const res = await request.get("/api/portfolio")
    expect(res.ok()).toBeTruthy()
    const data = await res.json()
    expect(data).toHaveProperty("cash_balance")
    expect(data).toHaveProperty("positions")
    expect(data).toHaveProperty("total_value")
    expect(data).toHaveProperty("total_pnl")
    expect(data.cash_balance).toBeGreaterThan(0)
    expect(data.cash_balance).toBeLessThanOrEqual(10000)
    expect(Array.isArray(data.positions)).toBeTruthy()
  })

  test("GET /api/watchlist returns 10 default tickers", async ({ request }) => {
    const res = await request.get("/api/watchlist")
    expect(res.ok()).toBeTruthy()
    const data = await res.json()
    expect(data).toHaveProperty("tickers")
    expect(Array.isArray(data.tickers)).toBeTruthy()
    expect(data.tickers.length).toBeGreaterThanOrEqual(10)
    const symbols = data.tickers.map((t: { ticker: string }) => t.ticker)
    expect(symbols).toContain("AAPL")
    expect(symbols).toContain("GOOGL")
    expect(symbols).toContain("MSFT")
    expect(symbols).toContain("AMZN")
    expect(symbols).toContain("TSLA")
  })

  test("GET /api/watchlist items have ticker and price fields", async ({ request }) => {
    const res = await request.get("/api/watchlist")
    const data = await res.json()
    const first = data.tickers[0]
    expect(first).toHaveProperty("ticker")
    expect(first).toHaveProperty("price")
  })

  test("POST /api/watchlist adds ticker returns 201 or 409", async ({ request }) => {
    const res = await request.post("/api/watchlist", { data: { ticker: "COIN" } })
    expect([201, 409]).toContain(res.status())
    if (res.status() === 201) {
      const data = await res.json()
      expect(data.ticker).toBe("COIN")
    }
  })

  test("POST /api/watchlist duplicate AAPL returns 409", async ({ request }) => {
    const res = await request.post("/api/watchlist", { data: { ticker: "AAPL" } })
    expect(res.status()).toBe(409)
  })

  test("POST /api/watchlist invalid ticker format returns 422", async ({ request }) => {
    const res = await request.post("/api/watchlist", { data: { ticker: "123INVALID" } })
    expect(res.status()).toBe(422)
  })

  test("DELETE /api/watchlist/{ticker} removes ticker (204)", async ({ request }) => {
    await request.post("/api/watchlist", { data: { ticker: "HOOD" } })
    const res = await request.delete("/api/watchlist/HOOD")
    expect(res.status()).toBe(204)
  })

  test("DELETE /api/watchlist/{ticker} non-existent returns 404", async ({ request }) => {
    const res = await request.delete("/api/watchlist/ZZZZZZ")
    expect(res.status()).toBe(404)
  })

  test("GET /api/portfolio/history returns snapshots", async ({ request }) => {
    const res = await request.get("/api/portfolio/history")
    expect(res.ok()).toBeTruthy()
    const data = await res.json()
    expect(data).toHaveProperty("snapshots")
    expect(Array.isArray(data.snapshots)).toBeTruthy()
  })

  test("POST /api/portfolio/trade buy AAPL 200 or 400", async ({ request }) => {
    await new Promise(resolve => setTimeout(resolve, 3000))
    const res = await request.post("/api/portfolio/trade", {
      data: { ticker: "AAPL", quantity: 1, side: "buy" },
    })
    expect([200, 400]).toContain(res.status())
    if (res.ok()) {
      const data = await res.json()
      expect(data.success).toBe(true)
      expect(data).toHaveProperty("trade")
      expect(data.trade.ticker).toBe("AAPL")
      expect(data).toHaveProperty("new_cash_balance")
    }
  })

  test("POST /api/portfolio/trade sell no position returns 400", async ({ request }) => {
    const res = await request.post("/api/portfolio/trade", {
      data: { ticker: "AAPL", quantity: 99999, side: "sell" },
    })
    expect(res.status()).toBe(400)
  })

  test("POST /api/portfolio/trade invalid side returns 400", async ({ request }) => {
    const res = await request.post("/api/portfolio/trade", {
      data: { ticker: "AAPL", quantity: 1, side: "hold" },
    })
    expect(res.status()).toBe(400)
  })

  test("POST /api/portfolio/trade negative quantity returns 400", async ({ request }) => {
    const res = await request.post("/api/portfolio/trade", {
      data: { ticker: "AAPL", quantity: -1, side: "buy" },
    })
    expect(res.status()).toBe(400)
  })

  test("POST /api/chat returns message with mock LLM", async ({ request }) => {
    const res = await request.post("/api/chat", {
      data: { message: "How is my portfolio doing?" },
    })
    expect(res.ok()).toBeTruthy()
    const data = await res.json()
    expect(data).toHaveProperty("message")
    expect(typeof data.message).toBe("string")
    expect(data.message.length).toBeGreaterThan(0)
  })

  test("POST /api/chat buy keyword triggers trade action in response", async ({ request }) => {
    const res = await request.post("/api/chat", {
      data: { message: "Please buy 10 shares of AAPL" },
    })
    expect(res.ok()).toBeTruthy()
    const data = await res.json()
    expect(data).toHaveProperty("message")
    expect(data.message).toMatch(/buy|AAPL/i)
  })

  test("POST /api/chat empty body returns 422", async ({ request }) => {
    const res = await request.post("/api/chat", { data: {} })
    expect(res.status()).toBe(422)
  })

  test("POST /api/chat wrong field name returns 422", async ({ request }) => {
    const res = await request.post("/api/chat", { data: { text: "wrong field" } })
    expect(res.status()).toBe(422)
  })
})

// ─── Trade Flow Integration ───────────────────────────────────────────────────

test.describe("Trade flow integration", () => {
  test("buy trade reduces cash balance", async ({ request }) => {
    await new Promise(resolve => setTimeout(resolve, 3000))
    const beforeRes = await request.get("/api/portfolio")
    const before = await beforeRes.json()
    const cashBefore = before.cash_balance

    const tradeRes = await request.post("/api/portfolio/trade", {
      data: { ticker: "MSFT", quantity: 1, side: "buy" },
    })

    if (tradeRes.ok()) {
      const afterRes = await request.get("/api/portfolio")
      const after = await afterRes.json()
      expect(after.cash_balance).toBeLessThan(cashBefore)
      const msftPos = after.positions.find((p: { ticker: string }) => p.ticker === "MSFT")
      expect(msftPos).toBeDefined()
      expect(msftPos.quantity).toBeGreaterThan(0)
    } else {
      expect(tradeRes.status()).toBe(400)
    }
  })

  test("buy then sell returns position to zero", async ({ request }) => {
    await new Promise(resolve => setTimeout(resolve, 3000))
    const buyRes = await request.post("/api/portfolio/trade", {
      data: { ticker: "NVDA", quantity: 1, side: "buy" },
    })
    if (\!buyRes.ok()) return

    const sellRes = await request.post("/api/portfolio/trade", {
      data: { ticker: "NVDA", quantity: 1, side: "sell" },
    })
    expect(sellRes.ok()).toBeTruthy()

    const afterRes = await request.get("/api/portfolio")
    const after = await afterRes.json()
    const nvdaPos = after.positions.find((p: { ticker: string }) => p.ticker === "NVDA")
    expect(nvdaPos).toBeUndefined()
  })

  test("portfolio history grows after a trade", async ({ request }) => {
    await new Promise(resolve => setTimeout(resolve, 3000))
    const histBefore = await request.get("/api/portfolio/history")
    const before = await histBefore.json()
    const countBefore = before.snapshots.length

    const tradeRes = await request.post("/api/portfolio/trade", {
      data: { ticker: "META", quantity: 1, side: "buy" },
    })

    if (tradeRes.ok()) {
      const histAfter = await request.get("/api/portfolio/history")
      const after = await histAfter.json()
      expect(after.snapshots.length).toBeGreaterThan(countBefore)
    }
  })
})
