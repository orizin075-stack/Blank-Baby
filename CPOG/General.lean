import CPOG.Check

/-!
General proof kernel for CPOG epistemic potentialism.

This file upgrades the finite countermodels to reusable propositions:
* directedness implies the modal .2 instance;
* a persistent split refutes .2;
* raw prefix histories with distinct first actions have no common extension;
* a FirstCommit distinction survives every abstraction that preserves it;
* unrestricted Subsumption fails whenever D preserves a predicate but G can defeat it;
* G-added negative FDE evidence defeats a positive-only view even when the raw decision record is unchanged.
-/

namespace CPOG.EpistemicPotentialism

section RelationalModal

variable {W : Type}

/-- Relational box. -/
def BoxR (R : W → W → Prop) (φ : W → Prop) (w : W) : Prop :=
  ∀ u, R w u → φ u

/-- Relational diamond. -/
def DiaR (R : W → W → Prop) (φ : W → Prop) (w : W) : Prop :=
  ∃ u, R w u ∧ φ u

/-- The modal .2 instance `◇□φ → □◇φ` at a world. -/
def DotTwoR (R : W → W → Prop) (φ : W → Prop) (w : W) : Prop :=
  DiaR R (BoxR R φ) w → BoxR R (DiaR R φ) w

/-- Local directedness/convergence above `w`. -/
def DirectedAt (R : W → W → Prop) (w : W) : Prop :=
  ∀ u v, R w u → R w v → ∃ z, R u z ∧ R v z

/-- Directedness is sufficient for the .2 instance at `w`. -/
theorem dotTwo_of_directedAt
    (R : W → W → Prop) (φ : W → Prop) (w : W)
    (hdir : DirectedAt R w) : DotTwoR R φ w := by
  intro hdia
  rcases hdia with ⟨u, hwu, hbox⟩
  intro v hwv
  rcases hdir u v hwu hwv with ⟨z, huz, hvz⟩
  exact ⟨z, hvz, hbox z huz⟩

/--
A persistent split is sufficient to refute the .2 instance: one accessible branch
makes `φ` permanently true and another makes `φ` permanently false.
-/
theorem not_dotTwo_of_persistent_split
    (R : W → W → Prop) (φ : W → Prop) (root a b : W)
    (hra : R root a) (hrb : R root b)
    (hA : ∀ u, R a u → φ u)
    (hB : ∀ u, R b u → ¬ φ u) :
    ¬ DotTwoR R φ root := by
  intro hdot
  have hdiaBox : DiaR R (BoxR R φ) root := ⟨a, hra, hA⟩
  have hboxDia : BoxR R (DiaR R φ) root := hdot hdiaBox
  rcases hboxDia b hrb with ⟨u, hbu, hφu⟩
  exact hB u hbu hφu

end RelationalModal

/-! ## Raw ordered histories -/

section RawHistories

variable {A : Type}

/-- `k` extends history `h` by appending a finite tail. -/
def HistExtends (h k : List A) : Prop :=
  ∃ tail, k = h ++ tail

/-- A history has first action `a`. -/
def FirstActionIs (a : A) (h : List A) : Prop :=
  ∃ tail, h = a :: tail

/-- Prefix extension preserves the first action. -/
theorem firstAction_persistent
    (a : A) {h k : List A}
    (hfirst : FirstActionIs a h)
    (hext : HistExtends h k) :
    FirstActionIs a k := by
  rcases hfirst with ⟨t, rfl⟩
  rcases hext with ⟨u, rfl⟩
  exact ⟨t ++ u, by simp⟩

/-- Distinct one-step branches of a raw list history have no common extension. -/
theorem distinct_first_actions_no_common_extension
    {a b : A} (hab : a ≠ b) :
    ¬ ∃ k, HistExtends [a] k ∧ HistExtends [b] k := by
  rintro ⟨k, ⟨ta, hta⟩, ⟨tb, htb⟩⟩
  have heq : a :: ta = b :: tb := by
    simpa using hta.symm.trans htb
  exact hab (List.cons.inj heq).1

/-- Empty history extends to every one-step history. -/
theorem empty_extends_singleton (a : A) : HistExtends [] [a] := by
  exact ⟨[a], by simp⟩

/-- Every extension of `[a]` still has first action `a`. -/
theorem singleton_branch_first_persistent (a : A) :
    ∀ k, HistExtends [a] k → FirstActionIs a k := by
  intro k hk
  exact firstAction_persistent a ⟨[], rfl⟩ hk

/-- Every extension of a distinct `[b]` branch fails `FirstActionIs a`. -/
theorem singleton_other_branch_first_false
    {a b : A} (hab : a ≠ b) :
    ∀ k, HistExtends [b] k → ¬ FirstActionIs a k := by
  intro k hk hfirstA
  rcases hk with ⟨tb, hkb⟩
  rcases hfirstA with ⟨ta, hka⟩
  have heq : a :: ta = b :: tb := by
    calc
      a :: ta = k := hka.symm
      _ = b :: tb := by simpa using hkb
  exact hab (List.cons.inj heq).1

/-- Raw ordered history already refutes .2 once two distinct first actions branch. -/
theorem raw_prefix_dotTwo_fails
    {a b : A} (hab : a ≠ b) :
    ¬ DotTwoR HistExtends (FirstActionIs a) [] := by
  apply not_dotTwo_of_persistent_split HistExtends (FirstActionIs a) [] [a] [b]
  · exact empty_extends_singleton a
  · exact empty_extends_singleton b
  · exact singleton_branch_first_persistent a
  · exact singleton_other_branch_first_false hab

end RawHistories

/-! ## FirstCommit and semantic abstraction -/

section FirstCommit

variable {H C : Type}

/-- An abstraction/equivalence respects an observed predicate if equivalent histories agree on it. -/
def RespectsPredicate (E : H → H → Prop) (P : H → Prop) : Prop :=
  ∀ x y, E x y → (P x ↔ P y)

/-- Two branches converge modulo an abstraction if successors can be identified by it. -/
def ConvergesModulo (G E : H → H → Prop) (x y : H) : Prop :=
  ∃ u v, G x u ∧ G y v ∧ E u v

/--
A persistent semantic distinction blocks convergence under every abstraction that preserves
that distinction. This is the abstract form of "FirstCommit divergence survives semantic
abstraction".
-/
theorem persistent_split_survives_abstraction
    (G E : H → H → Prop) (P : H → Prop) (a b : H)
    (hA : ∀ u, G a u → P u)
    (hB : ∀ u, G b u → ¬ P u)
    (hrespect : RespectsPredicate E P) :
    ¬ ConvergesModulo G E a b := by
  rintro ⟨u, v, hau, hbv, huv⟩
  have hPu : P u := hA u hau
  have hPv : P v := (hrespect u v huv).mp hPu
  exact hB v hbv hPv

/-- FirstCommit class is represented as a stable optional code. -/
def FirstCommitIs (first : H → Option C) (c : C) (h : H) : Prop :=
  first h = some c

/--
If branch A permanently records first commit `ca`, branch B permanently records a distinct
first commit `cb`, then no abstraction preserving the `ca` observation can make the branches
converge.
-/
theorem firstCommit_divergence_survives_abstraction
    (G E : H → H → Prop) (first : H → Option C)
    (a b : H) (ca cb : C) (hc : ca ≠ cb)
    (hA : ∀ u, G a u → first u = some ca)
    (hB : ∀ u, G b u → first u = some cb)
    (hrespect : RespectsPredicate E (FirstCommitIs first ca)) :
    ¬ ConvergesModulo G E a b := by
  apply persistent_split_survives_abstraction G E (FirstCommitIs first ca) a b
  · intro u hau
    exact hA u hau
  · intro u hbu hEq
    have hSome : some cb = some ca := (hB u hbu).symm.trans hEq
    exact hc (Option.some.inj hSome.symm)
  · exact hrespect

end FirstCommit

/-! ## Subsumption -/

section Subsumption

variable {W : Type}

/-- Local CPOG-style Subsumption instance. -/
def SubsumptionAt (D G : W → W → Prop) (φ : W → Prop) (w : W) : Prop :=
  BoxR D φ w → BoxR G φ w

/--
General failure theorem: if D keeps `φ` throughout all its accessible continuations,
but G has an accessible counterexample, then Subsumption fails at `w`.
-/
theorem not_subsumption_of_D_stable_G_defeater
    (D G : W → W → Prop) (φ : W → Prop) (w : W)
    (hD : BoxR D φ w)
    (hG : DiaR G (fun u => ¬ φ u) w) :
    ¬ SubsumptionAt D G φ w := by
  intro hSub
  have hBoxG : BoxR G φ w := hSub hD
  rcases hG with ⟨v, hGv, hNot⟩
  exact hNot (hBoxG v hGv)

end Subsumption

/-! ## Generic FDE defeat lemmas -/

/-- Adding explicit negative support always destroys positive-only status. -/
theorem join_negative_not_positiveOnly (ev : Evidence) :
    positiveOnly (joinEvidence ev evF) = false := by
  cases ev with
  | mk p n =>
      cases p <;> cases n <;> rfl

/-- A recorded positive resolution is effectively reopened after negative support is added. -/
theorem positive_resolution_reopens_after_negative_join (ev : Evidence) :
    effectiveDecision (joinEvidence ev evF) .resolvedPos = .contested := by
  cases ev with
  | mk p n =>
      cases p <;> cases n <;> rfl

/-- The derived current view is never positive-only after a G-added negative defeater. -/
theorem defeated_positive_resolution_not_positiveOnly (ev : Evidence) :
    positiveOnly (decideView (joinEvidence ev evF) .resolvedPos) = false := by
  cases ev with
  | mk p n =>
      cases p <;> cases n <;> rfl

/--
Generic content-level Subsumption failure. D keeps the derived view positive-only,
while G can reach a state whose evidence is the old evidence joined with explicit
negative support, with the raw decision record still `resolvedPos`.
-/
theorem content_subsumption_failure_of_G_defeat
    {W : Type}
    (D G : W → W → Prop)
    (evidence : W → Evidence)
    (decision : W → DecisionRecord)
    (w : W) (base : Evidence)
    (hD : ∀ u, D w u → positiveOnly (decideView (evidence u) (decision u)) = true)
    (hG : ∃ v, G w v ∧ evidence v = joinEvidence base evF ∧ decision v = .resolvedPos) :
    ¬ SubsumptionAt D G
      (fun u => positiveOnly (decideView (evidence u) (decision u)) = true) w := by
  apply not_subsumption_of_D_stable_G_defeater D G
    (fun u => positiveOnly (decideView (evidence u) (decision u)) = true) w
  · exact hD
  · rcases hG with ⟨v, hGv, hev, hdec⟩
    refine ⟨v, hGv, ?_⟩
    intro htrue
    have hfalse : positiveOnly (decideView (evidence v) (decision v)) = false := by
      rw [hev, hdec]
      exact defeated_positive_resolution_not_positiveOnly base
    rw [hfalse] at htrue
    cases htrue

/--
A concrete abstraction-map corollary: if an abstraction q preserves the FirstCommit-A
observation, the A/B branches cannot acquire a common abstract successor.
-/
theorem firstCommit_no_common_abstract_successor
    {H C Q : Type}
    (G : H → H → Prop) (first : H → Option C) (q : H → Q)
    (a b : H) (ca cb : C) (hc : ca ≠ cb)
    (hA : ∀ u, G a u → first u = some ca)
    (hB : ∀ u, G b u → first u = some cb)
    (hq : ∀ x y, q x = q y →
      (FirstCommitIs first ca x ↔ FirstCommitIs first ca y)) :
    ¬ ∃ u v, G a u ∧ G b v ∧ q u = q v := by
  exact firstCommit_divergence_survives_abstraction
    G (fun x y => q x = q y) first a b ca cb hc hA hB hq

/-! ## Generic modal recovery laws -/

/-- Reflexivity validates the T axiom. -/
theorem box_T_of_reflexive
    {W : Type} (R : W → W → Prop)
    (hrefl : ∀ w, R w w)
    (φ : W → Prop) (w : W) :
    BoxR R φ w → φ w := by
  intro hbox
  exact hbox w (hrefl w)

/-- Transitivity validates the 4 axiom. -/
theorem box_four_of_transitive
    {W : Type} (R : W → W → Prop)
    (htrans : ∀ x y z, R x y → R y z → R x z)
    (φ : W → Prop) (w : W) :
    BoxR R φ w → BoxR R (BoxR R φ) w := by
  intro hbox u hwu v huv
  exact hbox v (htrans w u v hwu huv)

/-- Reflexive and transitive accessibility validates the S4 frame laws used here. -/
theorem S4_frame_laws
    {W : Type} (R : W → W → Prop)
    (hrefl : ∀ w, R w w)
    (htrans : ∀ x y z, R x y → R y z → R x z)
    (φ : W → Prop) (w : W) :
    (BoxR R φ w → φ w) ∧
    (BoxR R φ w → BoxR R (BoxR R φ) w) := by
  exact ⟨box_T_of_reflexive R hrefl φ w,
    box_four_of_transitive R htrans φ w⟩

/-- Restricted Subsumption recovery for a G-stable predicate. -/
theorem subsumption_of_G_stable
    {W : Type} (D G : W → W → Prop) (φ : W → Prop) (w : W)
    (hDrefl : D w w)
    (hGstable : ∀ u, G w u → φ w → φ u) :
    SubsumptionAt D G φ w := by
  intro hboxD u hGu
  have hφw : φ w := hboxD w hDrefl
  exact hGstable u hGu hφw

end CPOG.EpistemicPotentialism
