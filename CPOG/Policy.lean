import CPOG.Provenance

namespace CPOG.Policy

open CPOG.SemanticProvenance

universe uI uS

variable {ι : Type uI} {S : Type uS}

/-- A source-policy family as Boolean observations. -/
def policyObservations (P : ι → S → Bool) : ObservationSystem ι S where
  Out := fun _ => Bool
  observe := fun i s => P i s

/-- Policy indistinguishability is exactly observational indistinguishability. -/
def PolicyEq (P : ι → S → Bool) (s t : S) : Prop :=
  ∀ i, P i s = P i t

theorem policyEq_iff_obsEq
    (P : ι → S → Bool) (s t : S) :
    PolicyEq P s t ↔ ObsEq (policyObservations P) s t := by
  rfl

/--
Any abstraction adequate for all selected source policies can only merge policy-equivalent
sources. This is the source-policy specialization of semantic minimal provenance.
-/
theorem adequate_source_abstraction_refines_policyEq
    {B : Type} (P : ι → S → Bool) (A : S → B)
    (hA : Adequate (policyObservations P) A) :
    ∀ ⦃s t⦄, Kernel A s t → PolicyEq P s t := by
  intro s t hst
  exact hA hst

/-- Open-ended safety against every Boolean policy collapses indistinguishability to equality. -/
theorem all_boolean_policies_separate [DecidableEq S] (s t : S) :
    (∀ P : S → Bool, P s = P t) ↔ s = t := by
  constructor
  · intro hall
    by_cases hst : s = t
    · exact hst
    · have h := hall (fun x => decide (x = s))
      have hts : t ≠ s := Ne.symm hst
      simp [hst, hts] at h
  · intro h
    subst t
    intro P
    rfl

/--
Hence if the future policy horizon is completely open-ended over Boolean policies, raw source
identity is the coarsest safe source representation.
-/
theorem open_ended_policy_safety_requires_identity [DecidableEq S]
    {B : Type} (A : S → B)
    (hA : ∀ ⦃s t⦄, A s = A t → ∀ P : S → Bool, P s = P t) :
    Function.Injective A := by
  intro s t hst
  exact (all_boolean_policies_separate s t).mp (hA hst)

end CPOG.Policy
