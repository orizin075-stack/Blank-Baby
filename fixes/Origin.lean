import Std
import CPOG.Provenance

namespace CPOG.EpistemicPotentialism.Origin

open CPOG.SemanticProvenance

structure PossibilityToken (Event Content Source : Type) where
  origin : Event
  content : Content
  source : Source
  deriving Repr

def tokenOf {Event Content Source : Type}
    (e : Event) (c : Content) (s : Source) : PossibilityToken Event Content Source :=
  ⟨e, c, s⟩

theorem distinct_origins_distinct_tokens {Event Content Source : Type}
    {e₁ e₂ : Event} {c : Content} {s : Source}
    (hne : e₁ ≠ e₂) :
    tokenOf e₁ c s ≠ tokenOf e₂ c s := by
  intro htok
  apply hne
  exact congrArg PossibilityToken.origin htok

def contentSourceObs {Event Content Source : Type} :
    ObservationSystem Unit (PossibilityToken Event Content Source) where
  Out := fun _ => Content × Source
  observe := fun _ t => (t.content, t.source)

theorem origin_difference_can_be_forgotten {Event Content Source : Type}
    (e₁ e₂ : Event) (c : Content) (s : Source) :
    ObsEq (contentSourceObs (Event := Event) (Content := Content) (Source := Source))
      (tokenOf e₁ c s) (tokenOf e₂ c s) := by
  intro i
  cases i
  rfl

def originObs {Event Content Source : Type} :
    ObservationSystem Unit (PossibilityToken Event Content Source) where
  Out := fun _ => Event
  observe := fun _ t => t.origin

theorem origin_audit_preserves_distinction {Event Content Source : Type}
    {e₁ e₂ : Event} {c : Content} {s : Source}
    (hne : e₁ ≠ e₂) :
    ¬ ObsEq (originObs (Event := Event) (Content := Content) (Source := Source))
      (tokenOf e₁ c s) (tokenOf e₂ c s) := by
  intro hObs
  apply hne
  have hEq := hObs ()
  change e₁ = e₂ at hEq
  exact hEq

def PolicyEq {I Source : Type} (P : I → Source → Bool) (s₁ s₂ : Source) : Prop :=
  ∀ i, P i s₁ = P i s₂

def policyObs {I Event Content Source : Type}
    (P : I → Source → Bool) :
    ObservationSystem I (PossibilityToken Event Content Source) where
  Out := fun _ => Content × Bool
  observe := fun i t => (t.content, P i t.source)

theorem policy_equivalent_sources_are_observation_equivalent
    {I Event Content Source : Type}
    (P : I → Source → Bool)
    {s₁ s₂ : Source}
    (hpol : PolicyEq P s₁ s₂)
    (e₁ e₂ : Event) (c : Content) :
    ObsEq (policyObs (Event := Event) (Content := Content) P)
      (tokenOf e₁ c s₁) (tokenOf e₂ c s₂) := by
  intro i
  change (c, P i s₁) = (c, P i s₂)
  rw [hpol i]

theorem all_boolean_policies_separate_sources
    {Source : Type} [DecidableEq Source] {s₁ s₂ : Source}
    (h : ∀ P : Source → Bool, P s₁ = P s₂) :
    s₁ = s₂ := by
  by_cases heq : s₁ = s₂
  · exact heq
  · exfalso
    have hsep := h (fun s => decide (s = s₁))
    have hs21 : s₂ = s₁ := by
      simpa using hsep
    exact heq hs21.symm

end CPOG.EpistemicPotentialism.Origin
