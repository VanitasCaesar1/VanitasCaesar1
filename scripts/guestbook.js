// Signs the guestbook: called by .github/workflows/guestbook.yml with the
// github-script context. Visitor text is reduced to plain words before it
// touches the README, so nobody can inject links, HTML or table breaks.

const fs = require("fs");

const INSTRUCTIONS = "Write your message in the title after";
const MAX_SHOWN = 6;

function clean(text, max) {
  return (text || "")
    .replace(/<!--[\s\S]*?-->/g, " ")
    .replace(/https?:\/\/\S+/gi, " ")
    .replace(/[\r\n\t]+/g, " ")
    .replace(/[<>\[\]()`*_~|#!\\{}=@^$%&]/g, "")
    .replace(/\s+/g, " ")
    .trim()
    .slice(0, max)
    .trim();
}

module.exports = async ({ github, context }) => {
  const issue = context.payload.issue;
  const { owner, repo } = context.repo;
  const login = issue.user.login; // GitHub logins are letters, digits and hyphens.

  const body = (issue.body || "").includes(INSTRUCTIONS) ? "" : issue.body;
  const message =
    clean(issue.title.replace(/^\s*guestbook\s*:?/i, ""), 140) || clean(body, 140);

  const reply = async (text) => {
    await github.rest.issues.createComment({ owner, repo, issue_number: issue.number, body: text });
    await github.rest.issues.update({ owner, repo, issue_number: issue.number, state: "closed", state_reason: "completed" });
  };

  if (!message) {
    await reply("Looks like the message was empty. Open a new issue titled `Guestbook: your message` and I'll add you.");
    return false;
  }

  const entries = JSON.parse(fs.readFileSync("guestbook.json", "utf8"));
  entries.unshift({ login, message, date: issue.created_at, issue: issue.number });
  fs.writeFileSync("guestbook.json", JSON.stringify(entries, null, 2) + "\n");

  const fmt = (iso) =>
    new Date(iso).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric", timeZone: "Asia/Kolkata" });
  const rows = entries
    .slice(0, MAX_SHOWN)
    .map((e) => `| [${e.login}](https://github.com/${e.login}) | ${e.message} | ${fmt(e.date)} |`);
  const table = ["| Visitor | Message | Signed |", "| --- | --- | --- |", ...rows].join("\n");
  const more = entries.length > MAX_SHOWN ? `\n\n<sub>${entries.length} signatures so far. Every one is in guestbook.json.</sub>` : "";

  const readme = fs.readFileSync("README.md", "utf8");
  const start = "<!-- GUESTBOOK:START -->";
  const end = "<!-- GUESTBOOK:END -->";
  const before = readme.slice(0, readme.indexOf(start) + start.length);
  const after = readme.slice(readme.indexOf(end));
  fs.writeFileSync("README.md", `${before}\n${table}${more}\n${after}`);

  await reply(`Thanks for signing my guestbook, ${login}! You're on my profile now: https://github.com/${owner}`);
  return true;
};
