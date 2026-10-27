// Counts my Treato commits for the commit counter: every non-merge commit since
// March 2025 on every branch of the Treato repos, each SHA counted once.
// The repos are private, so this runs in a GitHub Action with a read-only token
// (secret TREATO_STATS_TOKEN). Prints the total; COUNT_JSON=1 prints a breakdown.
const TOKEN = process.env.TREATO_STATS_TOKEN || process.env.GH_TOKEN;
const OWNER = "VanitasCaesar1";
const REPOS = [
  "backendgo", "treato-health", "treato-m-new", "treato-clinic", "treato-website",
  "treato-auth", "treato-landing", "treato-chat", "treato-livekit",
];
const SINCE = "2025-03-01T00:00:00Z";

if (!TOKEN) {
  console.error("TREATO_STATS_TOKEN is not set");
  process.exit(1);
}

async function gql(query, variables) {
  for (let attempt = 1; ; attempt++) {
    const res = await fetch("https://api.github.com/graphql", {
      method: "POST",
      headers: { Authorization: `bearer ${TOKEN}`, "Content-Type": "application/json" },
      body: JSON.stringify({ query, variables }),
    });
    const body = await res.json().catch(() => ({}));
    if (res.ok && !body.errors) return body.data;
    if (attempt === 3) throw new Error(`GitHub API: ${res.status} ${JSON.stringify(body.errors || body)}`);
    await new Promise((r) => setTimeout(r, 2000 * attempt));
  }
}

const BRANCHES = `query($owner: String!, $name: String!, $after: String) {
  repository(owner: $owner, name: $name) {
    defaultBranchRef { name }
    refs(refPrefix: "refs/heads/", first: 100, after: $after) {
      pageInfo { hasNextPage endCursor }
      nodes { name target { oid } }
    }
  }
}`;

const HISTORY = `query($owner: String!, $name: String!, $ref: String!, $since: GitTimestamp!, $after: String) {
  repository(owner: $owner, name: $name) {
    ref(qualifiedName: $ref) {
      target {
        ... on Commit {
          history(since: $since, first: 100, after: $after) {
            pageInfo { hasNextPage endCursor }
            nodes { oid parents { totalCount } }
          }
        }
      }
    }
  }
}`;

async function countRepo(name) {
  let branches = [], defaultBranch, after = null;
  do {
    const { repository } = await gql(BRANCHES, { owner: OWNER, name, after });
    defaultBranch = repository.defaultBranchRef?.name;
    branches.push(...repository.refs.nodes);
    after = repository.refs.pageInfo.hasNextPage ? repository.refs.pageInfo.endCursor : null;
  } while (after);
  // Default branch first: most other branches are already merged into it.
  branches.sort((a, b) => (b.name === defaultBranch) - (a.name === defaultBranch));

  const seen = new Set();
  let commits = 0;
  for (const branch of branches) {
    // A branch whose tip was already counted adds nothing new.
    if (seen.has(branch.target.oid)) continue;
    let cursor = null;
    do {
      const { repository } = await gql(HISTORY, {
        owner: OWNER, name, ref: `refs/heads/${branch.name}`, since: SINCE, after: cursor,
      });
      const history = repository.ref?.target?.history;
      if (!history) break;
      for (const c of history.nodes) {
        if (seen.has(c.oid)) continue;
        seen.add(c.oid);
        if (c.parents.totalCount < 2) commits++;
      }
      cursor = history.pageInfo.hasNextPage ? history.pageInfo.endCursor : null;
    } while (cursor);
  }
  return commits;
}

const perRepo = {};
for (const name of REPOS) perRepo[name] = await countRepo(name);
const total = Object.values(perRepo).reduce((a, b) => a + b, 0);
if (process.env.COUNT_JSON) console.log(JSON.stringify({ total, perRepo }, null, 2));
else console.log(total);
