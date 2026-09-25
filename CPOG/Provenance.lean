import CPOG.General

/-!
Semantic-observation-induced minimal provenance.

The theorem is deliberately representation-neutral: an observation family determines an
indistinguishability relation and a complete semantic signature. Every abstraction that is
adequate for those observations has a kernel finer than observational equivalence, and the
semantic signature factors through the reachable image of that abstraction.
-/

namespace CPOG.SemanticProvenance

universe uI uA uO uB

/-- Heterogeneous semantic observations over a carrier `α`. -/
structure ObservationSystem (ι : Type uI) (α : Type uA) where
  Out : ι → Type uO
  observe : (i : ι) → α → Out i

/-- Two carrier elements are indistinguishable by all selected observations. -/
def ObsEq {ι : Type uI} {α : Type uA}
    (O : ObservationSystem ι α) (x y : α) : Prop :=
  ∀ i, O.observe i x = O.observe i y

theorem obsEq_refl
    {ι : Type uI} {α : Type uA}
    (O : ObservationSystem ι α) (x : α) : ObsEq O x x := by
  intro i
  rfl

theorem obsEq_symm
    {ι : Type uI} {α : Type uA}
    {O : ObservationSystem ι α} {x y : α}
    (h : ObsEq O x y) : ObsEq O y x := by
  intro i
  exact (h i).symm

theorem obsEq_trans
    {ι : Type uI} {α : Type uA}
    {O : ObservationSystem ι α} {x y z : α}
    (hxy : ObsEq O x y) (hyz : ObsEq O y z) : ObsEq O x z := by
  intro i
  exact (hxy i).trans (hyz i)

/-- The complete observation signature. -/
def Signature {ι : Type uI} {α : Type uA}
    (O : ObservationSystem ι α) :=
  (i : ι) → O.Out i

/-- Compute the complete signature of one object. -/
def signature {ι : Type uI} {α : Type uA}
    (O : ObservationSystem ι α) (x : α) : Signature O :=
  fun i => O.observe i x

/-- Equality of complete signatures is exactly observation equivalence. -/
theorem signature_eq_iff_obsEq
    {ι : Type uI} {α : Type uA}
    (O : ObservationSystem ι α) (x y : α) :
    signature O x = signature O y ↔ ObsEq O x y := by
  constructor
  · intro h i
    exact congrArg (fun f => f i) h
  · intro h
    funext i
    exact h i

/-- Kernel relation induced by an abstraction. -/
def Kernel {α : Type uA} {β : Type uB} (A : α → β) (x y : α) : Prop :=
  A x = A y

/-- `A` is adequate when it never merges a distinction visible to the selected observations. -/
def Adequate
    {ι : Type uI} {α : Type uA} {β : Type uB}
    (O : ObservationSystem ι α) (A : α → β) : Prop :=
  ∀ ⦃x y⦄, Kernel A x y → ObsEq O x y

/-- The canonical signature representation is itself adequate. -/
theorem signature_adequate
    {ι : Type uI} {α : Type uA}
    (O : ObservationSystem ι α) :
    Adequate O (signature O) := by
  intro x y h
  exact (signature_eq_iff_obsEq O x y).1 h

/--
Minimal provenance theorem in refinement form: the kernel of every adequate abstraction is
contained in observational equivalence. Equivalently, an adequate representation can merge
no more pairs than the semantic observation quotient does.
-/
theorem adequate_kernel_refines_obsEq
    {ι : Type uI} {α : Type uA} {β : Type uB}
    (O : ObservationSystem ι α) (A : α → β)
    (hA : Adequate O A) :
    ∀ ⦃x y⦄, Kernel A x y → ObsEq O x y := by
  intro x y hxy
  exact hA hxy

/--
Equivalent kernel statement using the canonical signature: every adequate abstraction is at
least as fine as signature equality.
-/
theorem adequate_kernel_refines_signature_kernel
    {ι : Type uI} {α : Type uA} {β : Type uB}
    (O : ObservationSystem ι α) (A : α → β)
    (hA : Adequate O A) :
    ∀ ⦃x y⦄, Kernel A x y → Kernel (signature O) x y := by
  intro x y hxy
  exact (signature_eq_iff_obsEq O x y).2 (hA hxy)

/-- Reachable image of an abstraction. -/
def Image {α : Type uA} {β : Type uB} (A : α → β) :=
  {b : β // ∃ x, A x = b}

/--
Universal factorization theorem: if `A` is adequate, then the semantic signature is a
function of the abstract value `A x` alone (on the reachable image of `A`).
-/
theorem signature_factors_through_every_adequate_abstraction
    {ι : Type uI} {α : Type uA} {β : Type uB}
    (O : ObservationSystem ι α) (A : α → β)
    (hA : Adequate O A) :
    ∃ h : Image A → Signature O,
      ∀ x, h ⟨A x, ⟨x, rfl⟩⟩ = signature O x := by
  classical
  let pick : Image A → α := fun b => Classical.choose b.property
  have hpick : ∀ b : Image A, A (pick b) = b.1 := by
    intro b
    exact Classical.choose_spec b.property
  let h : Image A → Signature O := fun b => signature O (pick b)
  refine ⟨h, ?_⟩
  intro x
  apply (signature_eq_iff_obsEq O _ _).2
  apply hA
  exact hpick ⟨A x, ⟨x, rfl⟩⟩

/--
The factor map is unique on the reachable image if one asks it to reproduce all original
signatures. This makes the canonical signature a terminal information content among such
factorizations, up to equality on reachable abstract states.
-/
theorem signature_factor_unique
    {ι : Type uI} {α : Type uA} {β : Type uB}
    (O : ObservationSystem ι α) (A : α → β)
    (h₁ h₂ : Image A → Signature O)
    (hh₁ : ∀ x, h₁ ⟨A x, ⟨x, rfl⟩⟩ = signature O x)
    (hh₂ : ∀ x, h₂ ⟨A x, ⟨x, rfl⟩⟩ = signature O x) :
    h₁ = h₂ := by
  funext b
  rcases b.property with ⟨x, hx⟩
  have hb : b = ⟨A x, ⟨x, rfl⟩⟩ := by
    apply Subtype.ext
    exact hx.symm
  rw [hb, hh₁ x, hh₂ x]

/-! ## The quotient itself -/

/-- Setoid induced exactly by the selected semantic observations. -/
def observationSetoid
    {ι : Type uI} {α : Type uA}
    (O : ObservationSystem ι α) : Setoid α where
  r := ObsEq O
  iseqv := ⟨obsEq_refl O, obsEq_symm, obsEq_trans⟩

/-- The literal semantic observation quotient X / ~O. -/
abbrev ObservationQuotient
    {ι : Type uI} {α : Type uA}
    (O : ObservationSystem ι α) :=
  Quotient (observationSetoid O)

/-- Canonical quotient map. -/
def quotientMap
    {ι : Type uI} {α : Type uA}
    (O : ObservationSystem ι α) (x : α) : ObservationQuotient O :=
  Quotient.mk (observationSetoid O) x

/-- Quotient equality is exactly semantic observational equivalence. -/
theorem quotientMap_eq_iff_obsEq
    {ι : Type uI} {α : Type uA}
    (O : ObservationSystem ι α) (x y : α) :
    quotientMap O x = quotientMap O y ↔ ObsEq O x y := by
  constructor
  · intro h
    exact Quotient.exact h
  · intro h
    exact Quotient.sound h

/-- The quotient map itself is adequate for all observations in O. -/
theorem quotientMap_adequate
    {ι : Type uI} {α : Type uA}
    (O : ObservationSystem ι α) :
    Adequate O (quotientMap O) := by
  intro x y h
  exact (quotientMap_eq_iff_obsEq O x y).1 h

/--
Direct coarseness theorem for Theorem 4 of the paper: every adequate abstraction has a
kernel contained in the kernel of the semantic quotient map.
-/
theorem adequate_kernel_refines_observationQuotient
    {ι : Type uI} {α : Type uA} {β : Type uB}
    (O : ObservationSystem ι α) (A : α → β)
    (hA : Adequate O A) :
    ∀ ⦃x y⦄, Kernel A x y → quotientMap O x = quotientMap O y := by
  intro x y hxy
  exact Quotient.sound (hA hxy)

/--
Universal factorization form: every adequate abstraction determines the semantic quotient
value on its reachable image. Thus the quotient forgets exactly the distinctions invisible
to O and no more.
-/
theorem observationQuotient_factors_through_every_adequate_abstraction
    {ι : Type uI} {α : Type uA} {β : Type uB}
    (O : ObservationSystem ι α) (A : α → β)
    (hA : Adequate O A) :
    ∃ h : Image A → ObservationQuotient O,
      ∀ x, h ⟨A x, ⟨x, rfl⟩⟩ = quotientMap O x := by
  classical
  let pick : Image A → α := fun b => Classical.choose b.property
  have hpick : ∀ b : Image A, A (pick b) = b.1 := by
    intro b
    exact Classical.choose_spec b.property
  let h : Image A → ObservationQuotient O := fun b => quotientMap O (pick b)
  refine ⟨h, ?_⟩
  intro x
  apply Quotient.sound
  apply hA
  exact hpick ⟨A x, ⟨x, rfl⟩⟩


end CPOG.SemanticProvenance
