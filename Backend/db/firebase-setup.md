# Firebase Setup & Local Emulator Guide

## Prerequisites

- [Node.js](https://nodejs.org/) v18+
- [Java JDK 11+](https://adoptium.net/) (required by the Firebase emulators)
- A Firebase project created at [console.firebase.google.com](https://console.firebase.google.com)

---

## One-Time Installation

```bash
npm install -g firebase-tools
firebase login
```

---

## One-Time Project Setup (already done — files committed in this folder)

If you are setting up from scratch, the following command was used to generate the config files in this folder:

```bash
cd Backend/db
firebase init
```

Selected services: **Firestore**, **Storage**, **Emulators**
Selected emulators: **Auth**, **Firestore**, **Storage**

---

## Running the Local Emulator

From the `Backend/db/` directory:

```bash
firebase emulators:start --import=./seed --export-on-exit=./seed
```

> The `.firebaserc` is pre-configured with `demo-cs5224` as the default project.
> The `demo-` prefix tells Firebase CLI to run in **fully offline demo mode** — no Google account or cloud project is required for local development.

| Service    | Local URL                    |
|------------|------------------------------|
| Emulator UI | http://localhost:4000       |
| Auth        | http://localhost:9099       |
| Firestore   | http://localhost:8080       |
| Storage     | http://localhost:9199       |

### Seeding Test Data

To import the seed data on startup:

```bash
firebase emulators:start --import=./seed --export-on-exit=./seed
```

- `--import=./seed` loads the fixture data from the `seed/` folder on startup
- `--export-on-exit=./seed` saves emulator state back to `seed/` when you stop it — useful for persisting test data across sessions

---

## Connecting Your App to the Emulator

In your backend/app initialisation code, add the following when running in development mode:

```js
// Example using Firebase JS SDK
import { connectFirestoreEmulator, getFirestore } from 'firebase/firestore';
import { connectAuthEmulator, getAuth } from 'firebase/auth';
import { connectStorageEmulator, getStorage } from 'firebase/storage';

const db = getFirestore();
const auth = getAuth();
const storage = getStorage();

if (process.env.NODE_ENV === 'development') {
  connectFirestoreEmulator(db, 'localhost', 8080);
  connectAuthEmulator(auth, 'http://localhost:9099');
  connectStorageEmulator(storage, 'localhost', 9199);
}
```

Use an `.env` file to control `NODE_ENV` — never hardcode it.

---

## Firestore Collections (mapped from schema)

| Collection        | Key Fields                                      | Notes                                      |
|-------------------|-------------------------------------------------|--------------------------------------------|
| `users`           | `email`, `district_id`, `points`, `badges`      | Auth UID used as document ID               |
| `transactions`    | `user_id`, `district_id`, `cv_result`, `is_counted` | Subcollection or top-level            |
| `recycling_bins`  | `inc_crc`, `location` (GeoPoint), `district_id` | Populated by batch sync job from data.gov.sg |
| `districts`       | `name`, `region`                                | Mostly static, seeded once                 |
| `leaderboard`     | `month`, `district_rankings[]`                  | Written by scheduled batch job             |

See `readme.md` in this folder for the full schema design.

---

## Files in This Folder

| File                     | Purpose                                           |
|--------------------------|---------------------------------------------------|
| `firebase.json`          | Emulator ports and Firestore/Storage rules config |
| `.firebaserc`            | Firebase project alias                            |
| `firestore.rules`        | Firestore security rules                          |
| `firestore.indexes.json` | Composite index definitions                       |
| `storage.rules`          | Cloud Storage security rules                      |
| `seed/`                  | Exported emulator data for local development      |

---

## .gitignore Notes

The following are excluded from the repo (see root `.gitignore`):

```
.firebase/
firebase-export-*/
firestore-debug.log
ui-debug.log
storage-debug.log
```
