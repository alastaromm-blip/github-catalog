/** In-sheet sync (Extensions > Apps Script): no service account needed.
 *  Setup: paste this file, set GITHUB_TOKEN in Script Properties, run fullSync().
 *  Sheet must have tab "catalog". Manual columns must be named manual_* (script never touches them).
 */
const HEADER = ["hub_ru","sub","full_name","url","desc_en","desc_ru","stars","forks","pushed_at","language","license","topics","active","updated_at","source"];
const HUBS = [
  {ru: "Видео и звук для постов", topics: ["video-editing","ffmpeg","text-to-speech","speech-to-text"]},
  {ru: "Боты для мессенджеров", topics: ["telegram-bot","discord-bot","chatbot"]},
  {ru: "Сбор данных с сайтов", topics: ["scraping","crawler"]},
  {ru: "Сайт без программиста", topics: ["landing-page","static-site","cms","ecommerce"]},
  {ru: "Таблицы и учет для себя", topics: ["dashboard","spreadsheet"]},
  {ru: "Основа для своего сервиса", topics: ["boilerplate","saas","stripe"]},
  {ru: "Помощники на нейросети", topics: ["ai-chatbot","rag","llm"]},
  {ru: "Свои сервисы вместо чужих", topics: ["self-hosted","analytics","cloud-storage"]},
  {ru: "Продвижение и автопомощники", topics: ["seo","automation","rss"]},
];
const MIN_STARS = 50, MAX_REPOS = 1000;

function token_() {
  const t = PropertiesService.getScriptProperties().getProperty("GITHUB_TOKEN");
  if (!t) throw new Error("Set GITHUB_TOKEN in Project Settings > Script Properties");
  return t;
}
function gh_(path) {
  const r = UrlFetchApp.fetch("https://api.github.com" + path, {
    headers: { Authorization: "Bearer " + token_(), Accept: "application/vnd.github+json" },
    muteHttpExceptions: true,
  });
  if (r.getResponseCode() === 200) return JSON.parse(r.getContentText());
  if (r.getResponseCode() === 403) { Utilities.sleep(60000); return gh_(path); }
  throw new Error(path + " -> " + r.getResponseCode() + " " + r.getContentText().slice(0, 200));
}
function fullSync() {
  const seen = {}, out = [];
  HUBS.forEach(h => h.topics.forEach(topic => {
    const q = encodeURIComponent(`topic:${topic} stars:>=${MIN_STARS} pushed:>=2024-01-01`);
    const data = gh_(`/search/repositories?q=${q}&sort=stars&order=desc&per_page=100`);
    (data.items || []).forEach(it => {
      const k = it.full_name.toLowerCase();
      if (!seen[k] && out.length < MAX_REPOS) { seen[k] = 1; out.push({hub: h.ru, full: it.full_name}); }
    });
    Utilities.sleep(2500);
  }));
  const rows = [HEADER];
  out.forEach(s => {
    try {
      const r = gh_(`/repos/${s.full}`);
      let topics = [];
      try { topics = (gh_(`/repos/${s.full}/topics`).names || []); } catch (e) {}
      rows.push([s.hub, "", r.full_name, r.html_url, r.description || "", "",
        r.stargazers_count, r.forks_count, r.pushed_at, r.language || "",
        (r.license || {}).spdx_id || "", topics.join(","), "да",
        new Date().toISOString(), "api-apps-script"]);
    } catch (e) { Logger.log("skip " + s.full + ": " + e); }
    Utilities.sleep(600);
  });
  const ws = SpreadsheetApp.getActive().getSheetByName("catalog") || SpreadsheetApp.getActive().insertSheet("catalog");
  ws.clear();
  ws.getRange(1, 1, rows.length, HEADER.length).setValues(rows);
  Logger.log("wrote " + (rows.length - 1));
}
function quickUpdate() {
  const ws = SpreadsheetApp.getActive().getSheetByName("catalog");
  const v = ws.getDataRange().getValues(), H = v[0];
  const cFull = H.indexOf("full_name"), cStars = H.indexOf("stars"), cPush = H.indexOf("pushed_at"), cUpd = H.indexOf("updated_at");
  for (let i = 1; i < v.length; i++) {
    try {
      const r = gh_(`/repos/${v[i][cFull]}`);
      ws.getRange(i + 1, cStars + 1).setValue(r.stargazers_count);
      ws.getRange(i + 1, cPush + 1).setValue(r.pushed_at);
      ws.getRange(i + 1, cUpd + 1).setValue(new Date().toISOString());
    } catch (e) { Logger.log("skip row " + i + ": " + e); }
    Utilities.sleep(600);
    if (i % 50 === 0) SpreadsheetApp.flush();
  }
}
