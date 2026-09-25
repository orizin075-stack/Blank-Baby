from pathlib import Path
p = Path("CPOG_ProofComplete_v50/CPOG/Convergence.lean")
s = p.read_text()
s = s.replace("induction k with", "induction k generalizing x with")
s = s.replace("(σ : PropEvidence) (k : Nat) : PropEvidence :=", "(σ : PropEvidence (N := N)) (k : Nat) : PropEvidence (N := N) :=")
s = s.replace("(E : N → N → Prop) (σ : PropEvidence) (k : Nat) (x : N) :", "(E : N → N → Prop) (σ : PropEvidence (N := N)) (k : Nat) (x : N) :")
s = s.replace("(E : N → N → Prop) (σ : PropEvidence) (K : Nat)", "(E : N → N → Prop) (σ : PropEvidence (N := N)) (K : Nat)")
p.write_text(s)
