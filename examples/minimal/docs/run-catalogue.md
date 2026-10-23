# Run catalogue

### 1. Plants grow about 0.6 cm per week
*Notebook:* `notebooks/01_plants.ipynb` (§1) · *Code:* `analysis/growth.py` · *Results:* `results/growth/`

**Rationale.** We needed a baseline growth rate before testing fertiliser.

**Technical approach.** Height of 20 plants measured weekly for 4 weeks; linear fit per plant, plant as the unit.

**Results.** Mean slope 0.6 cm/week (95% CI 0.5–0.7).

**Caveats.** One greenhouse, one season.

### 2. Fertiliser raises yield by 1.3 kg
*Notebook:* `notebooks/01_plants.ipynb` (§2) · *Code:* `analysis/yield.py`

**Rationale.** Builds on §1: does fertiliser change the outcome that matters?

**Technical approach.** 10 plots per arm, randomised; plot as the unit; t-test.

**Results.** 3.4 vs 2.1 kg, difference 1.3 kg (p 0.01).

**Caveats.** Small trial.

### 3. Researchers sleep 7.6 hours
*Code:* `analysis/sleep.py` · *Results:* `results/sleep/`

**Rationale.** A control question with no connection to plants.

**Technical approach.** Seven self-reports.

**Results.** Mean 7.6 hours.

**Caveats.** Self-report.
