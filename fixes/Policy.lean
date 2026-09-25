import CPOG.Provenance

namespace CPOG.Policy

open CPOG.SemanticProvenance

universe uI uS
variable {I : Type uI} {Source : Type uS}

def PolicyEq (P : I → Source → Bool) (s t : Source) : Prop :=
  ∀ i, P i s = P i t

def policySignature (P : I → Source → Bool) (s : Source) : I → Bool :=
  fun i => P i s

theorem policySignature_eq_iff
    (P : I → Source → Bool) (s t : Source) :
    policySignature P s = policySignature P t ↔ PolicyEq P s t := by
  constructor
  · intro h i
    exact congrFun h i
  · intro h
    funext i
    exact h i

def sourcePolicyObservation (P : I → Source → Bool) : ObservationSystem I Source where
  Out := fun _ => Bool
  observe := P

theorem sourcePolicy_obsEq_iff
    (P : I → Source → Bool) (s t : Source) :
    ObsEq (sourcePolicyObservation P) s t ↔ PolicyEq P s t := by
  rfl

theorem openEnded_policy_safety_is_identity
    [DecidableEq Source] {s t : Source}
    (h : ∀ P : Source → Bool, P s = P t) :
    s = t := by
  by_cases heq : s = t
  · exact heq
  · exfalso
    have hsep := h (fun x => decide (x = s))
    have hts : t = s := by
      simpa using hsep
    exact heq hts.symm

def HorizonPolicyEq
    {H : Type} (J : H → Type) (P : (h : H) → J h → Source → Bool)
    (s t : Source) : Prop :=
  ∀ h j, P h j s = P h j t

end CPOG.Policy
