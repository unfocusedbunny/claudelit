# Check your own sessions

Were you in a hidden Claude Code experiment? This little script looks at the session files Claude Code saves on your computer and tells you.

```
python3 check_my_sessions.py
```

It shows two things:

**Right now:** the experiment ID Claude Code has cached for your account, per app and model, from `~/.claude.json`. No ID means no experiment.

**History:** it reads your saved sessions in `~/.claude/projects/*/*.jsonl` and prints one row per experiment ID, with how Opus 5.5 behaved for you:

- how often a reply used 2 or more tools
- how long its Bash commands were
- how long its answers and its thinking were
- which effort level was on

"none" means no experiment was active. Compare any other ID with "none" to see whether something changed.

**Nothing is sent anywhere.** The script reads numbers and IDs only, never your prompts or code. With `--csv summary.csv` it also saves the table as a file, which you can share if you want to. It holds numbers only.

IDs are shortened to their first 3 characters, the way people compare them online (`c0e`, `34e`). Use `--full-ids` for the whole thing.

Other options: `--by week` groups by week instead of experiment, `--dir PATH` and `--config PATH` if your files live somewhere else, `--model` for another model.

## Caveats

- Experiment IDs come from `clientDataCacheSlots` in `~/.claude.json` and from lines of type `atis-latch` in the session files. Claude Code could change either format any day.
- Method credit: u/WuM1ha1nho and u/DerAlbi on r/ClaudeCode worked out where the IDs live and which numbers to compare.
- "Answer tokens" are output tokens minus thinking tokens.
- Being in a test group doesn't mean the model got worse. It only means you got a different version of something.
