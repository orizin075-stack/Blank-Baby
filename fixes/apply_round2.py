from pathlib import Path

root = Path("CPOG_ProofComplete_v50/CPOG")

p = root / "Provenance.lean"
s = p.read_text()
s = s.replace("@[refl] theorem obsEq_refl", "theorem obsEq_refl")
s = s.replace("@[symm] theorem obsEq_symm", "theorem obsEq_symm")
s = s.replace("@[trans] theorem obsEq_trans", "theorem obsEq_trans")
s = s.replace(
    "(O : ObservationSystem ι α) : Type (max uI uO) :=\n  (i : ι) → O.Out i",
    "(O : ObservationSystem ι α) :=\n  (i : ι) → O.Out i",
)
p.write_text(s)

p = root / "Dynamics.lean"
s = p.read_text()
s = s.replace("exact hblock.trans hbase", "exact (hblock.trans hbase).symm")
s = s.replace("exact hblock.symm.trans hbase", "exact (hblock.symm.trans hbase).symm")
s = s.replace("exact hEq.trans hblock.symm", "exact hEq.symm.trans hblock.symm")
s = s.replace("exact hEq.trans hblock", "exact hEq.symm.trans hblock")
s = s.replace("(σ : PropEvidence) : Prop :=", "(σ : PropEvidence (N := N)) : Prop :=")
s = s.replace(
    "(σ : PropEvidence) : PropEvidence :=",
    "(σ : PropEvidence (N := N)) : PropEvidence (N := N) :=",
)
p.write_text(s)
