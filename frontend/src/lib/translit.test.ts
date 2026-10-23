import { describe, expect, it } from "vitest";
import { latnToCyrl, transliterateTree } from "./translit";

/** Latin → Cyrillic rules (reverse of backend §6). Pairs need native-speaker review. */
describe("latnToCyrl", () => {
  it.each([
    ["Oʻzbekiston", "Ўзбекистон"],
    ["gʻisht", "ғишт"],
    ["shahar", "шаҳар"],
    ["pochta", "почта"],
    ["yoʻq", "йўқ"],
    ["Yangi", "Янги"],
    ["yuborish", "юбориш"],
    ["yolgʻiz", "ёлғиз"],
    ["eski", "эски"],
    ["Elektron", "Электрон"],
    ["yer", "ер"],
    ["maʼlumot", "маълумот"],
    ["eʼlon", "эълон"],
    ["ketsa", "кетса"],
    ["Xizmat", "Хизмат"],
    ["SH", "Ш"],
    ["toʻgʻri", "тўғри"],
  ])("%s → %s", (latin, cyrillic) => {
    expect(latnToCyrl(latin)).toBe(cyrillic);
  });

  it("keeps placeholders, brands and domains", () => {
    expect(latnToCyrl("{count} ta belgi")).toBe("{count} та белги");
    expect(latnToCyrl("masalan siz@example.com.")).toBe("масалан siz@example.com.");
    expect(latnToCyrl("[PASSPORT] kabi")).toBe("[PASSPORT] каби");
    expect(latnToCyrl("GovAssist haqida")).toBe("GovAssist ҳақида");
    expect(latnToCyrl("lex.uz va my.gov.uz kabi")).toBe("lex.uz ва my.gov.uz каби");
    expect(latnToCyrl("Google orqali")).toBe("Google орқали");
  });

  it("maps a nested tree and keeps keys", () => {
    expect(transliterateTree({ a: { b: "Saqlash" }, c: "Til" })).toEqual({ a: { b: "Сақлаш" }, c: "Тил" });
  });

  it("keeps language endonyms", () => {
    expect(transliterateTree({ lang: { "uz-Latn": "Oʻzbekcha (lotin)", label: "Til" } })).toEqual({
      lang: { "uz-Latn": "Oʻzbekcha (lotin)", label: "Тил" },
    });
    expect(
      transliterateTree({
        lang: { name: { en: "English", "uz-Latn": "Oʻzbekcha" }, hint_latin: "Lotin yozuvi" },
      }),
    ).toEqual({
      lang: { name: { en: "English", "uz-Latn": "Oʻzbekcha" }, hint_latin: "Лотин ёзуви" },
    });
  });
});
