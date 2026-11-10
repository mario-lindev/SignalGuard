# SignalGuard

Uses phone-recorded pump sound to investigate early signs of failure and support maintenance in rural communities.

## Platform
Web, responsive to phone and desktop.

## Stack
Python standard library HTTP server and SQLite; vanilla HTML/CSS/JavaScript. Implementation choice based on available runtime. No cloud inference dependency.

## Product truth
Primary intended users are community pump caretakers and technicians (inferred from brief). All recordings are user-provided. No field validation or pretrained fault model is supplied. Anomaly scores require a verified healthy baseline; they are not diagnoses, water-quality measurements or failure-date predictions.
