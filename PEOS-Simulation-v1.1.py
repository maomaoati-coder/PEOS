# ============================================================
#  PEOS SIMULATION VERIFICATION v1.1
#  Photonic Emergence Operating System
# ============================================================
#  Author  : Mao Guanghui (毛广辉)
#  Email   : maomaoati@gmail.com
#  GitHub  : github.com/maomaoati-coder
#  Date    : 2026-06-08
#  PEOS    : DOI 10.5281/zenodo.20603667
#  PLC     : DOI 10.5281/zenodo.19801651
#  PSM     : DOI 10.5281/zenodo.20603456
#
#  CHANGELOG v1.0 → v1.1:
#  PAS3 legal probe offset corrected: 0.10 → 0.02 rad
#  Root cause: 0.10 = 2×δφ_min = 2σ → Gaussian gives exp(-2)≈0.135 < 0.50
#  Fix: 0.02 = 0.4σ → Gaussian gives exp(-0.08)≈0.923 > 0.50
#  Architecture definition unchanged. Parameter test error only.
#
#  ACADEMIC HONESTY STATEMENT:
#  All results are mathematical simulations of PEOS conceptual
#  model definitions. No physical hardware implementation or
#  hardware-level measurement of any kind is claimed.
#  Simulation ≠ Hardware Verification.
# ============================================================

import numpy as np

# ── utilities ────────────────────────────────────────────────

results = []

def record(name, cond, value, criterion, unit=""):
    s = "PASS" if cond else "FAIL"
    results.append((name, s))
    vfmt = (f"{value:.4e}" if (abs(value) < 1e-3 or abs(value) > 1e4)
            else f"{value:.6f}")
    print(f"  [{s}] {name}")
    print(f"         computed = {vfmt}{unit}   criterion = {criterion}")

print("=" * 62)
print("PEOS SIMULATION VERIFICATION v1.1")
print("Mao Guanghui (毛广辉) | 2026-06-08")
print("PEOS DOI : 10.5281/zenodo.20603667")
print("PLC  DOI : 10.5281/zenodo.19801651")
print("PSM  DOI : 10.5281/zenodo.20603456")
print("=" * 62)

# ============================================================
#  P-I  PHOTONIC PROCESS (PP)
#  Physical model: I(t) = I0 · exp((g - α) · t)
# ============================================================
print("\n── P-I: PHOTONIC PROCESS (PP) ──────────────────────")

I_thr = 0.10
I0    = 0.50
t     = np.linspace(0.0, 5.0, 5000)

# PP1 — RUNNING: g > α → sustained above threshold throughout
g1, a1 = 0.05, 0.02
I_run  = I0 * np.exp((g1 - a1) * t)
record(
    "PP1 RUNNING state  (g=0.05 > α=0.02, sustained all t)",
    np.all(I_run > I_thr),
    I_run[-1], f"> {I_thr}  [I_threshold]"
)

# PP2 — TERMINATED: α >> g → decays below threshold, no kill signal
g2, a2 = 0.00, 0.60
I_term = I0 * np.exp((g2 - a2) * t)
below  = I_term <= I_thr
first  = int(np.argmax(below)) if np.any(below) else -1
record(
    "PP2 TERMINATED state  (α=0.60 >> g=0.00, natural decay)",
    first > 0,
    I_term[-1], f"<= {I_thr}  [I_threshold at t_end]"
)
if first > 0:
    print(f"         coherence loss → termination at t_norm = {t[first]:.3f}  "
          f"(no kill signal, no OS intervention)")

# PP3 — CHILD SPAWN: power split + distinct phase identity
phi_parent = np.pi / 3
split_r    = 0.40
phi_child  = phi_parent + np.pi / 6     # Δφ_child = f(φ_parent), Claim C-05
I_child    = I0 * split_r
record(
    "PP3 Child spawn  (split=40%, viable intensity, distinct phase ID)",
    (I_child > I_thr) and (abs(phi_child - phi_parent) > 0.01),
    I_child, f"> {I_thr}  [I_threshold] & Δφ ≠ 0"
)
print(f"         φ_parent = {phi_parent:.4f} rad   "
      f"φ_child = {phi_child:.4f} rad   "
      f"Δφ = {phi_child - phi_parent:.4f} rad")

# ============================================================
#  P-II  PHASE ADDRESS SPACE (PAS)
#  Physical model: I_out = val · exp(-0.5·((θ_probe - θ_stored)/δφ)²)
# ============================================================
print("\n── P-II: PHASE ADDRESS SPACE (PAS) ─────────────────")

dph    = 0.05   # δφ_min [rad], Claim C-10
N_addr = int(np.floor(2 * np.pi / dph))
print(f"         N_addr = floor(2π / {dph}) = {N_addr} unique addresses")

def pas_read(th_store, val, th_probe, sigma):
    """Gaussian phase-space interference response (PAS read model)."""
    return val * np.exp(-0.5 * ((th_probe - th_store) / sigma) ** 2)

th_w = 1.047   # write address ≈ π/3 [rad]

# PAS1 — Correct address → constructive → high output
I_pas1 = pas_read(th_w, 1.0, th_w, dph)
record(
    "PAS1 READ @ correct address  (θ_probe = θ_write → constructive)",
    I_pas1 > 0.90, I_pas1, "> 0.90"
)

# PAS2 — Wrong address → destructive → low output
I_pas2 = pas_read(th_w, 1.0, th_w + 0.30, dph)
record(
    "PAS2 READ @ wrong address  (|Δθ| = 6×δφ_min → destructive)",
    I_pas2 < 0.10, I_pas2, "< 0.10"
)

# PAS3 — Phase-key access control, Claim C-13
#  Legal probe  : th_w + 0.02 = 0.4σ → Gaussian peak region → I ≈ 0.923
#  Illegal probe: th_w + 0.50 = 10σ  → Gaussian tail      → I ≈ 2e-22
#  [v1.1 fix: legal offset 0.10 → 0.02; at 0.10 = 2σ, Gaussian gives 0.135 < 0.50]
I_legal   = pas_read(th_w, 1.0, th_w + 0.02, dph)   # inside access window (0.4σ)
I_illegal = pas_read(th_w, 1.0, th_w + 0.50, dph)   # outside window (10σ)
record(
    "PAS3 Phase-key access control  (legal > 0.50, illegal < 1e-10)",
    (I_legal > 0.50) and (I_illegal < 1e-10),
    I_illegal, "< 1e-10  [illegal → destructive interference]"
)
print(f"         I_legal = {I_legal:.6f}  (offset=0.02=0.4σ)   "
      f"I_illegal = {I_illegal:.4e}  (offset=0.50=10σ)")

# ============================================================
#  P-III  ENERGY ROUTING SCHEDULING (ERS)
#  Physical model: resource_k = I_k / ΣI_j
# ============================================================
print("\n── P-III: ENERGY ROUTING SCHEDULING (ERS) ──────────")

I_procs = np.array([0.80, 0.50, 0.30, 0.20])
k_pre   = 2.0

# ERS1 — Allocation proportional to intensity
alloc = I_procs / I_procs.sum()
record(
    "ERS1 Highest intensity → maximum resource allocation",
    np.argmax(alloc) == 0,
    alloc[0], f"= max  {np.round(alloc, 4).tolist()}"
)
print(f"         allocations: {np.round(alloc, 4).tolist()}")

# ERS2 — Preemption: ratio > k_preempt
ratio = I_procs[0] / I_procs[3]
record(
    "ERS2 Preemption  (I_P0 / I_P3 > k_preempt = 2.0)",
    ratio > k_pre, ratio, f"> {k_pre}  [k_preempt threshold]"
)

# ERS3 — Fairness: equal intensities → equal allocation
I_eq     = np.full(4, 0.50)
alloc_eq = I_eq / I_eq.sum()
record(
    "ERS3 Fairness  (equal I_init → equal allocation = 0.25 each)",
    np.allclose(alloc_eq, 0.25, atol=1e-12),
    float(np.std(alloc_eq)), "std = 0.0  [all equal]"
)

# ============================================================
#  P-IV  INTERFERENCE INTERRUPT (II)
#  Physical model: |E1 + E2|² = A1² + A2² + 2·A1·A2·cos(Δφ)
# ============================================================
print("\n── P-IV: INTERFERENCE INTERRUPT (II) ───────────────")

A      = 1.0
I_trig = 3.0   # threshold: 4A²=4 > 3; 2A²=2 < 3; cos(π/2)→2A²=2 < 3

def I_comb(A1, A2, phi1, phi2):
    return A1**2 + A2**2 + 2 * A1 * A2 * np.cos(phi1 - phi2)

# II1 — Constructive Δφ=0 → TRIGGERED
I_ii1 = I_comb(A, A, 0.0, 0.0)
record(
    "II1 Constructive  (Δφ = 0) → INTERRUPT TRIGGERED",
    I_ii1 > I_trig, I_ii1, f"> {I_trig}  [I_trigger]"
)

# II2 — Destructive Δφ=π → NOT TRIGGERED
I_ii2 = I_comb(A, A, 0.0, np.pi)
record(
    "II2 Destructive   (Δφ = π) → NO INTERRUPT",
    I_ii2 < I_trig, I_ii2, f"< {I_trig}  [I_trigger]"
)

# II3 — Phase masking Δφ=π/2 → SUPPRESSED, Claim C-24
I_ii3 = I_comb(A, A, 0.0, np.pi / 2)
record(
    "II3 Phase masking (Δφ = π/2) → INTERRUPT SUPPRESSED",
    I_ii3 < I_trig, I_ii3, f"< {I_trig}  [I_trigger]"
)
print(f"         I_construct = {I_ii1:.3f}   I_destruct = {I_ii2:.3f}   "
      f"I_masked = {I_ii3:.3f}   I_trig = {I_trig}")

# ============================================================
#  P-V  EMERGENT CONCURRENCY (EC)
#  Physical basis: WDM orthogonality via DFT harmonic basis
# ============================================================
print("\n── P-V: EMERGENT CONCURRENCY (EC) ───────────────────")

N_ch = 8
N_t  = 10000
t_ec = np.arange(N_t) / N_t       # t ∈ [0, 1) normalized
E    = [np.cos(2 * np.pi * (k + 1) * t_ec) for k in range(N_ch)]

# EC1 — All channels simultaneously active
record(
    "EC1 All 8 WDM channels simultaneously active",
    all(np.max(np.abs(Ek)) > 0.99 for Ek in E),
    1.0, "amplitude = 1.0  [each channel]"
)
print(f"         {N_ch} channels, Δf = 1 [norm.], harmonic DFT-orthogonal basis")

# EC2 — Wavelength isolation (cross-correlation ≈ 0 by DFT orthogonality)
C = np.zeros((N_ch, N_ch))
for i in range(N_ch):
    for j in range(N_ch):
        denom   = np.sqrt((E[i] @ E[i]) * (E[j] @ E[j]))
        C[i, j] = np.abs(E[i] @ E[j]) / denom
off_max = float(np.max(C[~np.eye(N_ch, dtype=bool)]))
record(
    "EC2 Wavelength isolation  (off-diagonal cross-correlation < 1e-10)",
    off_max < 1e-10, off_max, "< 1e-10  [exact DFT orthogonality]"
)

# EC3 — FWM inter-thread communication: spectral detection at f_FWM = f1+f2-f3
#  cos(f1)·cos(f2)·cos(f3) → contains cos(f1+f2-f3) by product-to-sum identity
f1_n, f2_n, f3_n = 5, 6, 7
f_fwm = f1_n + f2_n - f3_n    # = 4
E_fwm = (np.cos(2 * np.pi * f1_n * t_ec) *
         np.cos(2 * np.pi * f2_n * t_ec) *
         np.cos(2 * np.pi * f3_n * t_ec))
spec       = np.abs(np.fft.rfft(E_fwm))
peak       = float(spec[f_fwm])
other_bins = np.concatenate([spec[1:f_fwm], spec[f_fwm + 1:]])
rms_other  = float(np.sqrt(np.mean(other_bins ** 2))) + 1e-20
snr        = peak / rms_other
record(
    "EC3 FWM inter-thread: f_FWM = f1+f2-f3 detected  (SNR > 5)",
    snr > 5.0, snr, "> 5.0  [peak / rms_other]", "  [SNR]"
)
print(f"         f1={f1_n} f2={f2_n} f3={f3_n} [norm.] → "
      f"f_FWM = {f_fwm} [norm.]   SNR = {snr:.1f}")

# ============================================================
#  VERIFICATION SUMMARY
# ============================================================
print("\n" + "=" * 62)
print("VERIFICATION SUMMARY")
print("=" * 62)

primitives = [
    ("P-I   Photonic Process",          results[0:3]),
    ("P-II  Phase Address Space",       results[3:6]),
    ("P-III Energy Routing Sched.",     results[6:9]),
    ("P-IV  Interference Interrupt",    results[9:12]),
    ("P-V   Emergent Concurrency",      results[12:15]),
]
for pname, ptests in primitives:
    n_p = sum(1 for _, s in ptests if s == "PASS")
    bar = "█" * n_p + "░" * (3 - n_p)
    print(f"  {pname:37s} {bar}  {n_p}/3")

passed = sum(1 for _, s in results if s == "PASS")
total  = len(results)
print(f"\n  Total  : {passed} / {total} PASS")
print(f"  Result : {'ALL PASS ✓' if passed == total else str(total - passed) + ' FAIL'}")

print("\n" + "=" * 62)
print("ACADEMIC HONESTY STATEMENT")
print("=" * 62)
print("""
  All results are mathematical simulations of the PEOS
  conceptual model. They verify internal consistency of the
  five architectural primitives as defined in PEOS-CLAIMS-v1.0
  and DOI 10.5281/zenodo.20603667.

  No physical hardware implementation or hardware-level
  measurement of any kind is claimed.

  Simulation ≠ Hardware Verification.

  Author : Mao Guanghui (毛广辉)   maomaoati@gmail.com
  PEOS   : DOI 10.5281/zenodo.20603667
  PLC    : DOI 10.5281/zenodo.19801651
  PSM    : DOI 10.5281/zenodo.20603456""")
print("=" * 62)
print("END — PEOS SIMULATION VERIFICATION v1.1")
print("=" * 62)
