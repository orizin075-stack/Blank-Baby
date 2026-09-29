namespace CPOG

/-!
# v57 observation-respecting maximal dynamic quotient and policy specialization

The raw bisimilarity quotient is the coarsest quotient that is dynamically
safe for the modal language.  When the manuscript also fixes an external
observation system O, the relevant object is the coarsest *observation-
respecting* dynamic equivalence.  This section constructs it directly as the
union, in existential form, of all G/D/H bisimulations that preserve O.

It also records the policy specialization of semantic minimality.
-/

universe u v w

def IsObservationBisimulation
    {W : Type u} {Atom : Type v} {I : Type w} {Y : Type}
    (M : Model W Atom) (O : I -> W -> Y)
    (Z : W -> W -> Prop) : Prop :=
  IsBisimulation M M Z /\
  forall {x y}, Z x y -> ObsEq O x y

def ObsBisimilar
    {W : Type u} {Atom : Type v} {I : Type w} {Y : Type}
    (M : Model W Atom) (O : I -> W -> Y) (x y : W) : Prop :=
  exists Z : W -> W -> Prop, IsObservationBisimulation M O Z /\ Z x y

theorem obsBisimilar_refl
    {W : Type u} {Atom : Type v} {I : Type w} {Y : Type}
    (M : Model W Atom) (O : I -> W -> Y) :
    forall x, ObsBisimilar M O x x := by
  intro x
  refine ⟨IdRel, ?_, rfl⟩
  constructor
  · exact identity_is_bisimulation M
  · intro a b hab
    subst b
    exact obsEq_refl O a

theorem obsBisimilar_symm
    {W : Type u} {Atom : Type v} {I : Type w} {Y : Type}
    {M : Model W Atom} {O : I -> W -> Y} {x y : W} :
    ObsBisimilar M O x y -> ObsBisimilar M O y x := by
  intro h
  rcases h with ⟨Z, hZ, hxy⟩
  refine ⟨Converse Z, ?_, hxy⟩
  constructor
  · exact converse_is_bisimulation hZ.1
  · intro a b hab
    exact obsEq_symm O (hZ.2 hab)

theorem obsBisimilar_trans
    {W : Type u} {Atom : Type v} {I : Type w} {Y : Type}
    {M : Model W Atom} {O : I -> W -> Y} {x y z : W} :
    ObsBisimilar M O x y ->
    ObsBisimilar M O y z ->
    ObsBisimilar M O x z := by
  intro hxy hyz
  rcases hxy with ⟨Z1, hZ1, hx1⟩
  rcases hyz with ⟨Z2, hZ2, h2z⟩
  refine ⟨RelComp Z1 Z2, ?_, ⟨y, hx1, h2z⟩⟩
  constructor
  · exact compose_is_bisimulation hZ1.1 hZ2.1
  · intro a c hac
    rcases hac with ⟨b, hab, hbc⟩
    exact obsEq_trans O (hZ1.2 hab) (hZ2.2 hbc)

theorem obsBisimilarity_is_bisimulation
    {W : Type u} {Atom : Type v} {I : Type w} {Y : Type}
    (M : Model W Atom) (O : I -> W -> Y) :
    IsBisimulation M M (ObsBisimilar M O) := by
  constructor
  · intro x y hxy a
    rcases hxy with ⟨Z, hZ, hrel⟩
    exact hZ.1.atom hrel a
  · intro x y hxy x' hxx'
    rcases hxy with ⟨Z, hZ, hrel⟩
    rcases hZ.1.forthG hrel hxx' with ⟨y', hyy', hxy'⟩
    exact ⟨y', hyy', ⟨Z, hZ, hxy'⟩⟩
  · intro x y hxy y' hyy'
    rcases hxy with ⟨Z, hZ, hrel⟩
    rcases hZ.1.backG hrel hyy' with ⟨x', hxx', hxy'⟩
    exact ⟨x', hxx', ⟨Z, hZ, hxy'⟩⟩
  · intro x y hxy x' hxx'
    rcases hxy with ⟨Z, hZ, hrel⟩
    rcases hZ.1.forthD hrel hxx' with ⟨y', hyy', hxy'⟩
    exact ⟨y', hyy', ⟨Z, hZ, hxy'⟩⟩
  · intro x y hxy y' hyy'
    rcases hxy with ⟨Z, hZ, hrel⟩
    rcases hZ.1.backD hrel hyy' with ⟨x', hxx', hxy'⟩
    exact ⟨x', hxx', ⟨Z, hZ, hxy'⟩⟩
  · intro x y hxy x' hxx'
    rcases hxy with ⟨Z, hZ, hrel⟩
    rcases hZ.1.forthH hrel hxx' with ⟨y', hyy', hxy'⟩
    exact ⟨y', hyy', ⟨Z, hZ, hxy'⟩⟩
  · intro x y hxy y' hyy'
    rcases hxy with ⟨Z, hZ, hrel⟩
    rcases hZ.1.backH hrel hyy' with ⟨x', hxx', hxy'⟩
    exact ⟨x', hxx', ⟨Z, hZ, hxy'⟩⟩

theorem obsBisimilarity_respects_observation
    {W : Type u} {Atom : Type v} {I : Type w} {Y : Type}
    {M : Model W Atom} {O : I -> W -> Y} {x y : W} :
    ObsBisimilar M O x y -> ObsEq O x y := by
  intro h
  rcases h with ⟨Z, hZ, hrel⟩
  exact hZ.2 hrel

def observationBisimilarityDynamicEquiv
    {W : Type u} {Atom : Type v} {I : Type w} {Y : Type}
    (M : Model W Atom) (O : I -> W -> Y) :
    DynamicEquiv M (ObsBisimilar M O) where
  refl := obsBisimilar_refl M O
  symm := obsBisimilar_symm
  trans := obsBisimilar_trans
  bisim := obsBisimilarity_is_bisimulation M O

theorem observationDynamicEquiv_refines_obsBisimilarity
    {W : Type u} {Atom : Type v} {I : Type w} {Y : Type}
    {M : Model W Atom} {O : I -> W -> Y}
    {E : W -> W -> Prop}
    (hE : DynamicEquiv M E)
    (hObs : forall {x y}, E x y -> ObsEq O x y) :
    forall {x y}, E x y -> ObsBisimilar M O x y := by
  intro x y hxy
  exact ⟨E, ⟨hE.bisim, hObs⟩, hxy⟩

def observationBisimilaritySetoid
    {W : Type u} {Atom : Type v} {I : Type w} {Y : Type}
    (M : Model W Atom) (O : I -> W -> Y) : Setoid W where
  r := ObsBisimilar M O
  iseqv := ⟨obsBisimilar_refl M O, obsBisimilar_symm, obsBisimilar_trans⟩

def ObsBisimQuot
    {W : Type u} {Atom : Type v} {I : Type w} {Y : Type}
    (M : Model W Atom) (O : I -> W -> Y) :=
  Quotient (observationBisimilaritySetoid M O)

def observationBisimilarityPresentation
    {W : Type u} {Atom : Type v} {I : Type w} {Y : Type}
    (M : Model W Atom) (O : I -> W -> Y) :
    QuotientPresentation W (ObsBisimQuot M O) (ObsBisimilar M O) where
  classOf := fun x => Quotient.mk (observationBisimilaritySetoid M O) x
  surj := by
    intro q
    refine Quotient.inductionOn q ?_
    intro x
    exact ⟨x, rfl⟩
  class_eq_iff := by
    intro x y
    constructor
    · intro h
      exact Quotient.exact h
    · intro h
      exact Quotient.sound h

theorem observation_bisimilarity_quotient_truth
    {W : Type u} {Atom : Type v} {I : Type w} {Y : Type}
    (M : Model W Atom) (O : I -> W -> Y)
    (phi : Formula Atom) (x : W) :
    Satisfies M x phi <->
      Satisfies
        (quotientModel M (observationBisimilarityPresentation M O))
        ((observationBisimilarityPresentation M O).classOf x)
        phi := by
  exact quotient_invariance
    (observationBisimilarityDynamicEquiv M O)
    (observationBisimilarityPresentation M O)
    phi x

theorem observation_bisimilarity_quotient_respects_observation
    {W : Type u} {Atom : Type v} {I : Type w} {Y : Type}
    (M : Model W Atom) (O : I -> W -> Y) :
    forall {x y},
      (observationBisimilarityPresentation M O).classOf x =
        (observationBisimilarityPresentation M O).classOf y ->
      ObsEq O x y := by
  intro x y hxy
  exact obsBisimilarity_respects_observation
    ((observationBisimilarityPresentation M O).class_eq_iff.mp hxy)

theorem observation_bisimilarity_quotient_is_coarsest_safe
    {W : Type u} {Atom : Type v} {I : Type w} {Y : Type}
    {M : Model W Atom} {O : I -> W -> Y}
    {E : W -> W -> Prop}
    (hE : DynamicEquiv M E)
    (hObs : forall {x y}, E x y -> ObsEq O x y) :
    forall {x y},
      E x y ->
      (observationBisimilarityPresentation M O).classOf x =
        (observationBisimilarityPresentation M O).classOf y := by
  intro x y hxy
  exact (observationBisimilarityPresentation M O).class_eq_iff.mpr
    (observationDynamicEquiv_refines_obsBisimilarity hE hObs hxy)

/-! ## Policy specialization -/

def PolicyEq
    {I : Type u} {S : Type v}
    (P : I -> S -> Bool) (s t : S) : Prop :=
  forall i, P i s = P i t

theorem policyEq_iff_obsEq
    {I : Type u} {S : Type v}
    (P : I -> S -> Bool) (s t : S) :
    PolicyEq P s t <-> ObsEq P s t := by
  rfl

theorem policy_preserving_relation_refines_policyEq
    {I : Type u} {S : Type v}
    (P : I -> S -> Bool) (E : S -> S -> Prop)
    (hPres : forall {s t}, E s t -> forall i, P i s = P i t) :
    forall {s t}, E s t -> PolicyEq P s t := by
  exact semantic_minimal_quotient P E hPres

theorem all_boolean_policies_separate
    {S : Type u} [DecidableEq S] (s t : S) :
    (forall P : S -> Bool, P s = P t) <-> s = t := by
  constructor
  · intro hall
    by_cases hst : s = t
    · exact hst
    · have h := hall (fun x => decide (x = s))
      have hts : t ≠ s := Ne.symm hst
      simp [hts] at h
  · intro h
    subst t
    intro P
    rfl

theorem open_ended_policy_safety_requires_identity
    {S : Type u} [DecidableEq S]
    {B : Type v} (A : S -> B)
    (hA : forall {s t}, A s = A t ->
      forall P : S -> Bool, P s = P t) :
    Function.Injective A := by
  intro s t hst
  exact (all_boolean_policies_separate s t).mp (hA hst)

end CPOG
