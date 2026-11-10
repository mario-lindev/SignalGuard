# SignalGuard research and field-validation plan

## What the evidence supports

Acoustic anomaly detection learns normal machine operating sounds and scores departures. The [DCASE 2020 Task 2 specification](https://dcase.community/challenge2020/task-unsupervised-detection-of-anomalous-sounds) includes pumps and normal-only training. It evaluates ranking with ROC-AUC and partial AUC, rather than claiming remaining useful life.

The original [MIMII paper](https://arxiv.org/abs/1909.09347) and [dataset](https://zenodo.org/records/3384388) provide normal and anomalous industrial sounds under background noise. These are useful benchmarks, not evidence of effectiveness on hand pumps, borehole installations, or arbitrary phones. Check source licenses before downloading or redistributing data; this repository bundles no dataset.

[Early Detection of Cavitation in Centrifugal Pumps Using Low-Cost Vibration and Sound Sensors](https://www.mdpi.com/2077-0472/13/8/1544) studies low-cost sensing for centrifugal irrigation pumps. This supports investigating affordable sensing, but does not validate this implementation, phone microphones, hand pumps, or failure-date predictions.

[MIMII DUE](https://arxiv.org/abs/2105.02702) directly studies shifts in operational and environmental conditions. Phone changes, placement, wind, motor speed, hydraulic head and demand can change sound without mechanical damage. Those are central validation concerns.

## Implemented baseline

The dependency-free prototype uses a diagonal Gaussian normality model. It extracts mean log energy, zero crossing rate, and six log normalized Goertzel spectral measurements from 256 ms windows. Each pump learns a feature mean and standard deviation from separate healthy recordings. Variance floors prevent zero-variance division. The deviation score is root-mean-square standardized feature distance, not a calibrated probability.

At least five verified healthy recordings unlock comparison; this is a software minimum, not a scientifically justified sample size. Twenty or more diverse recordings are recommended as a starting collection target, not as proof of adequacy. Provisional thresholds of 2 and 3 generate Watch and Changed sound. They are engineering defaults requiring calibration against held-out field data. The app intentionally reports no fault type or time-to-failure.

Linear interpolation resamples to 8 kHz for comparable features but is not a production anti-aliasing filter. Frequencies above 4 kHz can contaminate results. A production feature pipeline should use band-limited resampling, log-mel spectra and learned embeddings, evaluated against this small baseline. Coarse spectral samples can miss faults. Averaging discards transient information; add temporal dispersion and segment scoring if field evidence supports them.

## Collection protocol

1. Identify pump type, drive mechanism, maintenance history and installation. Start with one electrically driven pump family; do not mix hand pumps and centrifugal pumps into a single validated claim.
2. A technician verifies healthy operation. Obtain community consent and avoid recording conversations.
3. Record 10 seconds during steady operation, at a repeatable marked position around 30–50 cm away, without touching moving equipment. Repeat on different days and operating conditions. Distances are a proposed protocol to test, not a validated optimum.
4. Record device model, distance, background noise, pump load and environmental conditions. Obtain inspection outcomes for suspected changes. Never deliberately operate unsafe or damaged equipment to collect data.
5. Keep ambiguous labels separate and record actual repairs and subsequent findings. A changed sound can come from noise, installation changes or operating state.

## Evaluation before deployment

Split by installation and recording session; keep neighboring clips from the same recording together. Reserve unseen phones, communities and pump models for external testing. Fit scalers, feature decisions and thresholds on training/validation only. Compare a Gaussian baseline, nearest neighbors and a log-mel autoencoder with the same splits. Report ROC-AUC, partial AUC, precision/recall, false alarms per pump-month, event lead time and missed maintenance events, with uncertainty and subgroup results. Test silence, clipping, wind, speech and out-of-domain recordings. No performance measurements or field trials have been performed for this repository.

An early-warning claim requires prospective longitudinal outcomes: a detectable sound change must precede an independently confirmed maintenance event by useful time, at an acceptable false-alarm rate. Cross-sectional anomaly classification cannot establish that claim.

## Deployment and community considerations

Serve over HTTPS for phone microphone access. A phone browser needs network connectivity to the local server; this is not an offline phone app. The server needs no external network for analysis after installation. Raw audio is processed in memory and not saved; feature vectors and pump metadata remain in SQLite. Background voices can still enter uploaded audio. Add access control, encrypted transport/storage, retention controls, backup, audited roles and multilingual usability before a shared deployment. Do not expose the development server publicly. Keep routine physical inspection and independent water-quality testing.
