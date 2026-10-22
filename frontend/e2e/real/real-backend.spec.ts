/**
 * F3 journey against the real backend: signup → verify link from the backend's console email → onboarding →
 * a passport question streamed by Gemini into cards with sources → feedback; then a legal and an off-topic
 * question. Records each answer's SSE event order and screenshots in `test-results/real/`.
 */
import { execFileSync } from "node:child_process";
import { mkdirSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { expect, test, type Page } from "@playwright/test";
import { expectAccessible } from "../helpers";

/** Repo root, where `docker compose` finds the stack. */
const REPO_ROOT = fileURLToPath(new URL("../../../", import.meta.url));
/** Where the evidence goes. */
const OUT_DIR = fileURLToPath(new URL("../../test-results-real/", import.meta.url));
/** A Gemini answer, including retrieval, can take a while. */
const ANSWER_TIMEOUT_MS = 120_000;
/** How long to wait for the verification email in the backend log. */
const EMAIL_TIMEOUT_MS = 30_000;
/** Screenshot widths and the shortest screenshot height. */
const DESKTOP_WIDTH = 1440;
const PHONE_WIDTH = 375;
const SHOT_MIN_HEIGHT = 812;
/** Test-only password for the throwaway account (never a real credential). */
const TEST_PASSWORD = "Sinov-parol-2026!";

/**
 * The newest email-verification path the backend's console email backend printed since `since`.
 *
 * @param since ISO time to read the logs from.
 * @returns `/verify-email/<key>`, or `null` when no email arrived yet.
 */
function verifyPathFromLogs(since: string): string | null {
  const logs = execFileSync(
    "docker",
    ["compose", "logs", "--no-color", "--no-log-prefix", "--since", since, "backend"],
    {
      cwd: REPO_ROOT,
      encoding: "utf8",
    },
  );
  // The console backend prints the MIME message; undo quoted-printable soft breaks and `=` escapes.
  const text = logs.replace(/=\r?\n/g, "").replace(/=3D/gi, "=");
  const paths = [...text.matchAll(/\/verify-email\/([^\s"'<>]+)/g)].map(
    (match) => `/verify-email/${match[1] ?? ""}`,
  );
  return paths.at(-1) ?? null;
}

/**
 * Event names of the chat SSE stream in the order received.
 *
 * @param body The full `text/event-stream` body.
 * @returns The event names.
 */
function eventOrder(body: string): string[] {
  return [...body.matchAll(/^event: ?(\S+)/gm)].map((match) => match[1] ?? "");
}

/**
 * The `final` message's answer type in a stream body.
 *
 * @param body The full `text/event-stream` body.
 * @returns The answer type, or `null` when there was no final.
 */
function finalAnswerType(body: string): string | null {
  const final = /event: ?final\r?\ndata: ?(.+)/.exec(body)?.[1];
  if (!final) return null;
  const data = JSON.parse(final) as { message: { answer: { answer_type: string } | null } };
  return data.message.answer?.answer_type ?? null;
}

/**
 * Full-page screenshot with the viewport stretched to the page, so the sticky composer stays at the bottom.
 *
 * @param page The page.
 * @param name File name (without extension) in the evidence folder.
 * @param width Viewport width for this shot.
 */
async function shot(page: Page, name: string, width = DESKTOP_WIDTH): Promise<void> {
  const before = page.viewportSize();
  await page.setViewportSize({ width, height: SHOT_MIN_HEIGHT });
  const height = await page.evaluate(() => document.documentElement.scrollHeight);
  await page.setViewportSize({ width, height: Math.max(SHOT_MIN_HEIGHT, height) });
  await page.screenshot({ path: `${OUT_DIR}${name}.png` });
  if (before) await page.setViewportSize(before);
}

/**
 * Ask a question and wait for the stream to finish.
 *
 * @param page The page.
 * @param text The question.
 * @returns The event order and the final answer type.
 */
async function ask(page: Page, text: string): Promise<{ events: string[]; answerType: string | null }> {
  const streamed = page.waitForResponse(
    (response) => response.url().endsWith("/api/v1/chat") && response.request().method() === "POST",
    { timeout: ANSWER_TIMEOUT_MS },
  );
  const input = page.getByLabel("Savolingiz");
  await input.fill(text);
  await input.press("Enter");
  const body = await (await streamed).text();
  return { events: eventOrder(body), answerType: finalAnswerType(body) };
}

test("real backend: signup → verify → onboarding → streamed answers → feedback", async ({ page }) => {
  const evidence: Record<string, unknown> = {};
  const email = `f3-e2e-${String(Date.now())}@example.com`;
  const since = new Date(Date.now() - 1000).toISOString();

  await test.step("sign up with the Turnstile test key", async () => {
    await page.goto("/signup");
    await page.getByLabel("Elektron pochta").fill(email);
    await page.getByLabel("Parol", { exact: true }).fill(TEST_PASSWORD);
    const submit = page.getByRole("button", { name: "Hisob yaratish" });
    await expect(submit).toBeEnabled({ timeout: 30_000 });
    await submit.click();
    await expect(page.getByRole("heading", { name: "Pochtangizni tekshiring" })).toBeVisible();
  });

  await test.step("open the verification link from the console email", async () => {
    await expect.poll(() => verifyPathFromLogs(since), { timeout: EMAIL_TIMEOUT_MS }).not.toBeNull();
    const path = verifyPathFromLogs(since);
    if (!path) throw new Error("No verification email in the backend log");
    await page.goto(path);
    await expect(page.getByRole("heading", { name: "Elektron pochta tasdiqlandi" })).toBeVisible();
    await page.getByRole("button", { name: "Davom etish" }).click();
  });

  await test.step("onboard: language, region and district", async () => {
    await page.getByRole("button", { name: "Keyingi" }).click();
    await page.getByRole("combobox", { name: "Viloyat" }).click();
    await page.getByRole("option", { name: "Toshkent shahri" }).click();
    await page.getByRole("combobox", { name: "Tuman yoki shahar" }).click();
    await page
      .getByRole("option", { name: /Chilonzor/ })
      .first()
      .click();
    await page.getByRole("button", { name: "Saqlash va boshlash" }).click();
    await expect(page.getByRole("heading", { level: 1, name: /Salom!/ })).toBeVisible();
  });

  await test.step("passport question streams into cards with sources", async () => {
    const result = await ask(page, "Pasportimni qanday yangilayman?");
    evidence.passport = result;
    expect(result.events[0]).toBe("meta");
    expect(result.events.at(-2)).toBe("final");
    expect(result.events.at(-1)).toBe("done");
    await expect(page.getByText("Javob foydali boʻldimi?")).toBeVisible({ timeout: ANSWER_TIMEOUT_MS });
    if (result.answerType === "service" || result.answerType === "legal") {
      await expect(page.getByRole("heading", { name: "Manbalar" })).toBeVisible();
    }
    await expectAccessible(page);
    await shot(page, "passport-1440");
    await shot(page, "passport-375", PHONE_WIDTH);
  });

  await test.step("feedback 👍 is saved", async () => {
    const saved = page.waitForResponse((response) =>
      /\/api\/v1\/messages\/.+\/feedback$/.test(response.url()),
    );
    await page.getByRole("button", { name: "Ha, foydali" }).click();
    expect((await saved).status()).toBeLessThan(300);
    await expect(page.getByText("Rahmat! Fikringiz saqlandi.")).toBeVisible();
  });

  await test.step("legal question in a new chat", async () => {
    await page.goto("/");
    const result = await ask(page, "Oila kodeksiga koʻra nikoh yoshi necha yosh?");
    evidence.legal = result;
    expect(result.events.at(-1)).toBe("done");
    await expect(page.getByText("Javob foydali boʻldimi?")).toBeVisible({ timeout: ANSWER_TIMEOUT_MS });
    if (result.answerType === "legal") {
      await expect(page.getByRole("heading", { name: "Qonunda nima deyilgan" })).toBeVisible();
    }
    await shot(page, "legal-1440");
  });

  await test.step("off-topic question is refused without an office", async () => {
    await page.goto("/");
    const result = await ask(page, "Ertaga Toshkentda ob-havo qanday boʻladi?");
    evidence.offTopic = result;
    expect(result.answerType).toBe("off_topic");
    await expect(page.getByText(/davlat xizmatlari va Oʻzbekiston qonunlari/)).toBeVisible({
      timeout: ANSWER_TIMEOUT_MS,
    });
    await expect(page.getByRole("region", { name: "Qayerga borish kerak" })).toHaveCount(0);
    await shot(page, "off-topic-1440");
    await shot(page, "off-topic-375", PHONE_WIDTH);
  });

  mkdirSync(OUT_DIR, { recursive: true });
  writeFileSync(`${OUT_DIR}evidence.json`, `${JSON.stringify(evidence, null, 2)}\n`);
});
