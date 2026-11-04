# Prototype 01 — same-channel obedience search

**Date:** 22 October 2026

**Goal:** find an injection sentence that `Qwen2.5-1.5B-Instruct` obeys, while the quoted copy of that sentence is not obeyed.

**Result:** no pair. The model keeps summarising. The canary is mentioned only when the email says what the response should be, and even then the reply is still a summary.

**Image:** `demo.png`

**Replies:** `replies.json`
