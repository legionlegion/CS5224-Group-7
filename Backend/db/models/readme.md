# Firestore Data Models

This folder contains sample JSON documents for each Firestore collection.
They serve as the **reference shape** for backend code when reading and writing data.

## Notes
- In Firestore, `_id` is not stored as a field — it is the **document ID** set when creating the document.
- Timestamps should be stored as Firestore `Timestamp` objects (not plain strings) in actual code.
- Fields marked `// optional` may be absent in older documents — always use a default when reading.

## Collections

| File | Collection | Document ID |
|---|---|---|
| `user.json` | `users` | Firebase Auth UID (e.g. `uid_abc123`) |
| `transaction.json` | `transactions` | Auto-generated ID |
| `recycling_bin.json` | `recycling_bins` | `inc_crc` value from data.gov.sg |
| `district.json` | `districts` | District code (e.g. `SG-BS`) |
| `leaderboard.json` | `leaderboard` | Month string (e.g. `2025-01`) |
