namespace CPOG

/-!
# v57 greatest observation-safe dynamic quotient

This section restores, in the current unified kernel, the paper-level theorem
that there is a greatest G/D/H bisimulation respecting a chosen observation
system.  Its quotient is therefore the coarsest dynamically safe observation
quotient and preserves the full tri-modal language.
-/

universe u v w x

structure ObservationBisimulation
    {I : Type u} {W : Type v} {Y : Type w} {Atom : Type x}
    (M : Model W Atom) (O : I -> W -> Y) where
  Z : W -> W -> Prop
  bisim : IsBisimulation M M Z
  observation : forall {a b}, Z a b -> ObsEq O a b

def identityObservationBisimulation
    {I : Type u} {W : Type v} {Y : Type w} {Atom : Type x}
    (M : Model W Atom) (O : I -> W -> Y) :
    ObservationBisimulation M O where
  Z := Eq
  bisim := by
    constructor <;> intro a b hab
    · subst b
      intro atom
      rfl
    · subst b
      intro a' haa'
      exact ⟨a', haa', rfl⟩
    · subst b
      intro b' hbb'
      exact ⟨b', hbb', rfl⟩
    · subst b
      intro a' haa'
      exact ⟨a', haa', rfl⟩
    · subst b
      intro b' hbb'
      exact ⟨b', hbb', rfl⟩
    · subst b
      intro a' haa'
      exact ⟨a', haa', rfl⟩
    · subst b
      intro b' hbb'
      exact ⟨b', hbb', rfl⟩
  observation := by
    intro a b hab
    subst b
    exact obsEq_refl O a

def converseObservationBisimulation
    {I : Type u} {W : Type v} {Y : Type w} {Atom : Type x}
    {M : Model W Atom} {O : I -> W -> Y}
    (B : ObservationBisimulation M O) :
    ObservationBisimulation M O where
  Z := fun a b => B.Z b a
  bisim := by
    constructor
    · intro a b hab atom
      exact (B.bisim.atom hab atom).symm
    · intro a b hab a' haa'
      rcases B.bisim.backG hab haa' with ⟨b', hbb', hb'a'⟩
      exact ⟨b', hbb', hb'a'⟩
    · intro a b hab b' hbb'
      rcases B.bisim.forthG hab hbb' with ⟨a', haa', hb'a'⟩
      exact ⟨a', haa', hb'a'⟩
    · intro a b hab a' haa'
      rcases B.bisim.backD hab haa' with ⟨b', hbb', hb'a'⟩
      exact ⟨b', hbb', hb'a'⟩
    · intro a b hab b' hbb'
      rcases B.bisim.forthD hab hbb' with ⟨a', haa', hb'a'⟩
      exact ⟨a', haa', hb'a'⟩
    · intro a b hab a' haa'
      rcases B.bisim.backH hab haa' with ⟨b', hbb', hb'a'⟩
      exact ⟨b', hbb', hb'a'⟩
    · intro a b hab b' hbb'
      rcases B.bisim.forthH hab hbb' with ⟨a', haa', hb'a'⟩
      exact ⟨a', haa', hb'a'⟩
  observation := by
    intro a b hab
    exact obsEq_symm O (B.observation hab)

def composeObservationBisimulation
    {I : Type u} {W : Type v} {Y : Type w} {Atom : Type x}
    {M : Model W Atom} {O : I -> W -> Y}
    (B₁ B₂ : ObservationBisimulation M O) :
    ObservationBisimulation M O where
  Z := fun a c => exists b, B₁.Z a b /\ B₂.Z b c
  bisim := by
    constructor
    · intro a c hac atom
      rcases hac with ⟨b, hab, hbc⟩
      exact (B₁.bisim.atom hab atom).trans (B₂.bisim.atom hbc atom)
    · intro a c hac a' haa'
      rcases hac with ⟨b, hab, hbc⟩
      rcases B₁.bisim.forthG hab haa' with ⟨b', hbb', ha'b'⟩
      rcases B₂.bisim.forthG hbc hbb' with ⟨c', hcc', hb'c'⟩
      exact ⟨c', hcc', ⟨b', ha'b', hb'c'⟩⟩
    · intro a c hac c' hcc'
      rcases hac with ⟨b, hab, hbc⟩
      rcases B₂.bisim.backG hbc hcc' with ⟨b', hbb', hb'c'⟩
      rcases B₁.bisim.backG hab hbb' with ⟨a', haa', ha'b'⟩
      exact ⟨a', haa', ⟨b', ha'b', hb'c'⟩⟩
    · intro a c hac a' haa'
      rcases hac with ⟨b, hab, hbc⟩
      rcases B₁.bisim.forthD hab haa' with ⟨b', hbb', ha'b'⟩
      rcases B₂.bisim.forthD hbc hbb' with ⟨c', hcc', hb'c'⟩
      exact ⟨c', hcc', ⟨b', ha'b', hb'c'⟩⟩
    · intro a c hac c' hcc'
      rcases hac with ⟨b, hab, hbc⟩
      rcases B₂.bisim.backD hbc hcc' with ⟨b', hbb', hb'c'⟩
      rcases B₁.bisim.backD hab hbb' with ⟨a', haa', ha'b'⟩
      exact ⟨a', haa', ⟨b', ha'b', hb'c'⟩⟩
    · intro a c hac a' haa'
      rcases hac with ⟨b, hab, hbc⟩
      rcases B₁.bisim.forthH hab haa' with ⟨b', hbb', ha'b'⟩
      rcases B₂.bisim.forthH hbc hbb' with ⟨c', hcc', hb'c'⟩
      exact ⟨c', hcc', ⟨b', ha'b', hb'c'⟩⟩
    · intro a c hac c' hcc'
      rcases hac with ⟨b, hab, hbc⟩
      rcases B₂.bisim.backH hbc hcc' with ⟨b', hbb', hb'c'⟩
      rcases B₁.bisim.backH hab hbb' with ⟨a', haa', ha'b'⟩
      exact ⟨a', haa', ⟨b', ha'b', hb'c'⟩⟩
  observation := by
    intro a c hac
    rcases hac with ⟨b, hab, hbc⟩
    exact obsEq_trans O (B₁.observation hab) (B₂.observation hbc)

def ObsBisimilar
    {I : Type u} {W : Type v} {Y : Type w} {Atom : Type x}
    (M : Model W Atom) (O : I -> W -> Y) (a b : W) : Prop :=
  exists B : ObservationBisimulation M O, B.Z a b

theorem obsBisimilar_refl
    {I : Type u} {W : Type v} {Y : Type w} {Atom : Type x}
    (M : Model W Atom) (O : I -> W -> Y) (a : W) :
    ObsBisimilar M O a a :=
  ⟨identityObservationBisimulation M O, rfl⟩

theorem obsBisimilar_symm
    {I : Type u} {W : Type v} {Y : Type w} {Atom : Type x}
    {M : Model W Atom} {O : I -> W -> Y}
    {a b : W} :
    ObsBisimilar M O a b -> ObsBisimilar M O b a := by
  rintro ⟨B, hab⟩
  exact ⟨converseObservationBisimulation B, hab⟩

theorem obsBisimilar_trans
    {I : Type u} {W : Type v} {Y : Type w} {Atom : Type x}
    {M : Model W Atom} {O : I -> W -> Y}
    {a b c : W} :
    ObsBisimilar M O a b ->
    ObsBisimilar M O b c ->
    ObsBisimilar M O a c := by
  rintro ⟨B₁, hab⟩ ⟨B₂, hbc⟩
  exact ⟨composeObservationBisimulation B₁ B₂, ⟨b, hab, hbc⟩⟩

def greatestObservationBisimulation
    {I : Type u} {W : Type v} {Y : Type w} {Atom : Type x}
    (M : Model W Atom) (O : I -> W -> Y) :
    ObservationBisimulation M O where
  Z := ObsBisimilar M O
  bisim := by
    constructor
    · intro a b hab atom
      rcases hab with ⟨B, hB⟩
      exact B.bisim.atom hB atom
    · intro a b hab a' haa'
      rcases hab with ⟨B, hB⟩
      rcases B.bisim.forthG hB haa' with ⟨b', hbb', ha'b'⟩
      exact ⟨b', hbb', ⟨B, ha'b'⟩⟩
    · intro a b hab b' hbb'
      rcases hab with ⟨B, hB⟩
      rcases B.bisim.backG hB hbb' with ⟨a', haa', ha'b'⟩
      exact ⟨a', haa', ⟨B, ha'b'⟩⟩
    · intro a b hab a' haa'
      rcases hab with ⟨B, hB⟩
      rcases B.bisim.forthD hB haa' with ⟨b', hbb', ha'b'⟩
      exact ⟨b', hbb', ⟨B, ha'b'⟩⟩
    · intro a b hab b' hbb'
      rcases hab with ⟨B, hB⟩
      rcases B.bisim.backD hB hbb' with ⟨a', haa', ha'b'⟩
      exact ⟨a', haa', ⟨B, ha'b'⟩⟩
    · intro a b hab a' haa'
      rcases hab with ⟨B, hB⟩
      rcases B.bisim.forthH hB haa' with ⟨b', hbb', ha'b'⟩
      exact ⟨b', hbb', ⟨B, ha'b'⟩⟩
    · intro a b hab b' hbb'
      rcases hab with ⟨B, hB⟩
      rcases B.bisim.backH hB hbb' with ⟨a', haa', ha'b'⟩
      exact ⟨a', haa', ⟨B, ha'b'⟩⟩
  observation := by
    intro a b hab
    rcases hab with ⟨B, hB⟩
    exact B.observation hB

def greatestObservationDynamicEquiv
    {I : Type u} {W : Type v} {Y : Type w} {Atom : Type x}
    (M : Model W Atom) (O : I -> W -> Y) :
    DynamicEquiv M (ObsBisimilar M O) where
  refl := obsBisimilar_refl M O
  symm := obsBisimilar_symm
  trans := obsBisimilar_trans
  bisim := (greatestObservationBisimulation M O).bisim

theorem every_observation_dynamic_equiv_refines_greatest
    {I : Type u} {W : Type v} {Y : Type w} {Atom : Type x}
    {M : Model W Atom} {O : I -> W -> Y}
    {E : W -> W -> Prop}
    (hE : DynamicEquiv M E)
    (hObs : forall {a b}, E a b -> ObsEq O a b) :
    forall {a b}, E a b -> ObsBisimilar M O a b := by
  intro a b hab
  let B : ObservationBisimulation M O :=
    { Z := E
      bisim := hE.bisim
      observation := hObs }
  exact ⟨B, hab⟩

theorem greatest_observation_relation_respects_observation
    {I : Type u} {W : Type v} {Y : Type w} {Atom : Type x}
    (M : Model W Atom) (O : I -> W -> Y) :
    forall {a b}, ObsBisimilar M O a b -> ObsEq O a b :=
  (greatestObservationBisimulation M O).observation

def greatestObservationSetoid
    {I : Type u} {W : Type v} {Y : Type w} {Atom : Type x}
    (M : Model W Atom) (O : I -> W -> Y) : Setoid W where
  r := ObsBisimilar M O
  iseqv := ⟨obsBisimilar_refl M O, obsBisimilar_symm, obsBisimilar_trans⟩

abbrev GreatestObservationQuotient
    {I : Type u} {W : Type v} {Y : Type w} {Atom : Type x}
    (M : Model W Atom) (O : I -> W -> Y) :=
  Quotient (greatestObservationSetoid M O)

def greatestObservationClassOf
    {I : Type u} {W : Type v} {Y : Type w} {Atom : Type x}
    (M : Model W Atom) (O : I -> W -> Y) (a : W) :
    GreatestObservationQuotient M O :=
  Quotient.mk (greatestObservationSetoid M O) a

def greatestObservationPresentation
    {I : Type u} {W : Type v} {Y : Type w} {Atom : Type x}
    (M : Model W Atom) (O : I -> W -> Y) :
    QuotientPresentation W (GreatestObservationQuotient M O)
      (ObsBisimilar M O) where
  classOf := greatestObservationClassOf M O
  surj := by
    intro q
    refine Quotient.inductionOn q ?_
    intro a
    exact ⟨a, rfl⟩
  class_eq_iff := by
    intro a b
    constructor
    · intro h
      exact Quotient.exact h
    · intro h
      exact Quotient.sound h

theorem greatest_observation_quotient_refines_static_observation
    {I : Type u} {W : Type v} {Y : Type w} {Atom : Type x}
    (M : Model W Atom) (O : I -> W -> Y) :
    forall {a b : W},
      (greatestObservationPresentation M O).classOf a =
        (greatestObservationPresentation M O).classOf b ->
      ObsEq O a b := by
  intro a b hab
  have hDyn : ObsBisimilar M O a b :=
    (greatestObservationPresentation M O).class_eq_iff.mp hab
  exact greatest_observation_relation_respects_observation M O hDyn

theorem greatest_dynamic_observation_quotient_is_coarsest
    {I : Type u} {W : Type v} {Y : Type w} {Atom : Type x}
    {M : Model W Atom} {O : I -> W -> Y}
    {E : W -> W -> Prop}
    (hE : DynamicEquiv M E)
    (hObs : forall {a b}, E a b -> ObsEq O a b)
    {a b : W} (hab : E a b) :
    (greatestObservationPresentation M O).classOf a =
      (greatestObservationPresentation M O).classOf b := by
  apply (greatestObservationPresentation M O).class_eq_iff.mpr
  exact every_observation_dynamic_equiv_refines_greatest hE hObs hab

theorem greatest_dynamic_observation_quotient_is_safe
    {I : Type u} {W : Type v} {Y : Type w} {Atom : Type x}
    (M : Model W Atom) (O : I -> W -> Y) :
    (forall {a b : W},
      (greatestObservationPresentation M O).classOf a =
        (greatestObservationPresentation M O).classOf b ->
      ObsEq O a b) /\
    (forall (phi : Formula Atom) (a : W),
      Satisfies M a phi <->
        Satisfies
          (quotientModel M (greatestObservationPresentation M O))
          ((greatestObservationPresentation M O).classOf a) phi) := by
  constructor
  · exact greatest_observation_quotient_refines_static_observation M O
  · intro phi a
    exact quotient_invariance
      (greatestObservationDynamicEquiv M O)
      (greatestObservationPresentation M O)
      phi a

/-! ## FirstCommit divergence survives the coarsest safe quotient -/

def QuotientCommitRegion
    {W : Type u} {Q : Type v} {E : W -> W -> Prop} {Choice : Type w}
    (P : QuotientPresentation W Q E)
    (F : W -> Option Choice) (A : Choice) : Q -> Prop :=
  fun q => exists x, P.classOf x = q /\ F x = some A

theorem quotientCommitRegion_forwardInvariant
    {W : Type u} {Q : Type v} {E : W -> W -> Prop} {Choice : Type w}
    (P : QuotientPresentation W Q E)
    (R : Rel W) (F : W -> Option Choice) (A : Choice)
    (hPersist : FirstCommitPersistent R F)
    (hLabel : forall {x y}, E x y -> F x = F y) :
    ForwardInvariantRegion
      (quotientRel P R)
      (QuotientCommitRegion P F A) := by
  intro q q' hqq' hqA
  rcases hqq' with ⟨x, y, hxq, hyq', hxy⟩
  rcases hqA with ⟨u, huq, huA⟩
  have hxu : E x u := by
    apply P.class_eq_iff.mp
    exact hxq.trans huq.symm
  have hxA : F x = some A := (hLabel hxu).trans huA
  have hyA : F y = some A := hPersist hxy hxA
  exact ⟨y, hyq', hyA⟩

theorem quotientCommitRegions_exclusive
    {W : Type u} {Q : Type v} {E : W -> W -> Prop} {Choice : Type w}
    (P : QuotientPresentation W Q E)
    (F : W -> Option Choice) {A B : Choice}
    (hAB : A ≠ B)
    (hLabel : forall {x y}, E x y -> F x = F y) :
    MutuallyExclusiveRegions
      (QuotientCommitRegion P F A)
      (QuotientCommitRegion P F B) := by
  intro q hA hB
  rcases hA with ⟨x, hxq, hxA⟩
  rcases hB with ⟨y, hyq, hyB⟩
  have hxy : E x y := by
    apply P.class_eq_iff.mp
    exact hxq.trans hyq.symm
  have hsame : F x = F y := hLabel hxy
  have habSome : (some A : Option Choice) = some B :=
    hxA.symm.trans (hsame.trans hyB)
  exact hAB (Option.some.inj habSome)

theorem firstCommit_dot2_fails_on_greatest_observation_quotient
    {I : Type u} {W : Type v} {Y : Type w} {Atom : Type x}
    (M : Model W Atom) (O : I -> W -> Y)
    {Choice : Type}
    (F : W -> Option Choice)
    {root a b : W} {A B : Choice}
    (hPersist : FirstCommitPersistent M.rG F)
    (hAB : A ≠ B)
    (hra : M.rG root a) (hrb : M.rG root b)
    (ha : F a = some A) (hb : F b = some B)
    (hObserves : forall {x y}, ObsEq O x y -> F x = F y) :
    let P := greatestObservationPresentation M O
    Dia (quotientModel M P).rG
        (Box (quotientModel M P).rG (QuotientCommitRegion P F A))
        (P.classOf root) /\
    Not
      (Box (quotientModel M P).rG
        (Dia (quotientModel M P).rG (QuotientCommitRegion P F A))
        (P.classOf root)) := by
  let P := greatestObservationPresentation M O
  have hLabel : forall {x y}, ObsBisimilar M O x y -> F x = F y := by
    intro x y hxy
    exact hObserves
      (greatest_observation_relation_respects_observation M O hxy)
  apply persistent_incompatible_branches_dot2_failure
    (quotientModel M P).rG
    (QuotientCommitRegion P F A)
    (QuotientCommitRegion P F B)
  · exact quotientCommitRegion_forwardInvariant
      P M.rG F A hPersist hLabel
  · exact quotientCommitRegion_forwardInvariant
      P M.rG F B hPersist hLabel
  · exact quotientCommitRegions_exclusive P F hAB hLabel
  · exact ⟨root, a, rfl, rfl, hra⟩
  · exact ⟨root, b, rfl, rfl, hrb⟩
  · exact ⟨a, rfl, ha⟩
  · exact ⟨b, rfl, hb⟩

end CPOG
