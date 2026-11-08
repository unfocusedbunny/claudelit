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

Counting complaint words is rough, and two lines moving together doesn't mean one caused the other. The method is on the page under [M].

Made by Mimi, built with Claude. Test data by [LiveNerf](https://github.com/ninjahawk/livenerf) (MIT).
