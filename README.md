# Claudelit

I'm checking if Claude Opus 5.5 got worse, or if I'm imagining it.

Every day two little robots collect:

- **what people say**: issues on the Claude Code GitHub that complain about quality
- **what tests show**: daily scores from [LiveNerf](https://github.com/ninjahawk/livenerf)

The page puts both on one timeline: [unfocusedbunny.github.io/claudelit](https://unfocusedbunny.github.io/claudelit/)

## What's in here

| File | What it does |
|---|---|
| `collectors/github_issues.py` | counts new Claude Code issues per day, and the ones with a complaint word in the title |
| `collectors/livenerf.py` | copies LiveNerf's daily results |
| `.github/workflows/daily.yml` | wakes both robots every morning and saves the data |
| `data/` | everything the robots collected, plus a hand-made list of events |
| `index.html` | the page |
| `tools/check_my_sessions.py` | for Claude Code users: were you in a hidden experiment? |

Counting complaint words is rough, and two lines moving together doesn't mean one caused the other. The method is on the page under [M].

## Use Claude Code? Check your own sessions

Some people say they were put into hidden experiments that changed how Opus 5.5 works for them. This shows whether you were, and what changed:

```
python3 tools/check_my_sessions.py
```

It reads the session files on your own computer and sends nothing anywhere. More in [tools/README.md](tools/README.md).

Made by Mimi, built with Claude. An independent project, not affiliated with or endorsed by Anthropic.

## Licences

- The code is MIT (see `LICENSE`).
- `data/livenerf/` comes from [LiveNerf](https://github.com/ninjahawk/livenerf), MIT, see `data/livenerf/LICENSE`.
- Issue titles in `data/github/` belong to their authors and link back to the original issues. No usernames are stored.
