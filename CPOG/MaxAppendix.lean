import Mathlib.Data.Finset.Card
import CPOG.Closure
import CPOG.ModalPreservation

/-!
Formal support for Appendix A of the CPOG paper.

These results deliberately formalize only the modest claims made in the
appendix: free extension over one distinguished generator, finite processing of
a precomputed finite descriptor closure, execution of a jointly admissible
finite bundle, and preservation of the Core modal fragment behind a firewall.
-/

namespace CPOG.MaxAppendix

universe uA uX uD uM uW uV uAtom

/-! ## A.1 Free atomic extension -/

structure PointedExtension (A : Type uA) (X : Type uX) where
  old : A → X
  generator : X

def freeCarrier (A : Type uA) := Sum A Unit

def freeMap {A : Type uA} {X : Type uX}
    (E : PointedExtension A X) : freeCarrier A → X
  | .inl a => E.old a
  | .inr _ => E.generator

def IsExtensionMap {A : Type uA} {X : Type uX}
    (E : PointedExtension A X) (f : freeCarrier A → X) : Prop :=
  (∀ a, f (.inl a) = E.old a) ∧ f (.inr ()) = E.generator

/--
The carrier A-plus-one-generator is initial among extensions equipped with an
embedding of old elements and one distinguished new generator.
-/
theorem freeAtomicExtension_initial
    {A : Type uA} {X : Type uX} (E : PointedExtension A X) :
    ∃! f : freeCarrier A → X, IsExtensionMap E f := by
  refine ⟨freeMap E, ?_, ?_⟩
  · constructor
    · intro a
      rfl
    · rfl
  · intro g hg
    funext s
    cases s with
    | inl a =>
        simpa [freeMap] using hg.1 a
    | inr u =>
        cases u
        simpa [freeMap] using hg.2

/-! ## A.2 Finite processing closure and Seal -/

def processList {D : Type uD} [DecidableEq D] :
    List D → Finset D → Finset D
  | [], processed => processed
  | d :: ds, processed => processList ds (insert d processed)

theorem mem_processList_of_mem_current
    {D : Type uD} [DecidableEq D]
    (ds : List D) (processed : Finset D) {d : D}
    (hd : d ∈ processed) :
    d ∈ processList ds processed := by
  induction ds generalizing processed with
  | nil =>
      simpa [processList] using hd
  | cons a ds ih =>
      have hmem : d ∈ insert a processed := Finset.mem_insert_of_mem hd
      simpa [processList] using ih (processed := insert a processed) hmem

theorem mem_processList_of_mem_input
    {D : Type uD} [DecidableEq D]
    (ds : List D) (processed : Finset D) {d : D}
    (hd : d ∈ ds) :
    d ∈ processList ds processed := by
  induction ds generalizing processed with
  | nil =>
      simp at hd
  | cons a ds ih =>
      simp only [List.mem_cons] at hd
      rcases hd with hda | hdrest
      · subst a
        have hmem : d ∈ insert d processed := by simp
        exact mem_processList_of_mem_current ds (insert d processed) hmem
      · simpa [processList] using ih (processed := insert a processed) hdrest

def processFiniteClosure
    {D : Type uD} [Fintype D] [DecidableEq D]
    (processed : Finset D) : Finset D :=
  processList (Finset.univ.toList) processed

/--
Once the complete descriptor-processing closure is known to be finite, an
explicit schedule processing every member reaches Seal.
-/
theorem finiteProcessingClosure_reaches_seal
    {D : Type uD} [Fintype D] [DecidableEq D]
    (processed : Finset D) :
    processFiniteClosure processed = Finset.univ := by
  apply Finset.ext
  intro d
  constructor
  · intro _
    simp
  · intro _
    apply mem_processList_of_mem_input
    simp

theorem finiteProcessingClosure_schedule_length
    {D : Type uD} [Fintype D] [DecidableEq D] :
    (Finset.univ : Finset D).toList.length = Fintype.card D := by
  simp

/-! ## A.3 Jointly admissible finite Max extension -/

def applyBundle {M : Type uM} {D : Type uD}
    (extend : M → D → M) : M → List D → M
  | m, [] => m
  | m, d :: ds => applyBundle extend (extend m d) ds

def JointlyAdmissible {M : Type uM} {D : Type uD}
    (extend : M → D → M) (admissible : M → D → Prop) :
    M → List D → Prop
  | _, [] => True
  | m, d :: ds =>
      admissible m d ∧ JointlyAdmissible extend admissible (extend m d) ds

def MaxStep {M : Type uM} {D : Type uD}
    (extend : M → D → M) (admissible : M → D → Prop)
    (m n : M) : Prop :=
  ∃ d, admissible m d ∧ n = extend m d

/--
A jointly admissible finite bundle has an actual finite execution path to the
state obtained by applying the bundle.
-/
theorem jointlyAdmissible_executes
    {M : Type uM} {D : Type uD}
    (extend : M → D → M) (admissible : M → D → Prop)
    (m : M) (bundle : List D)
    (hjoint : JointlyAdmissible extend admissible m bundle) :
    CPOG.Closure.RTC (MaxStep extend admissible) m (applyBundle extend m bundle) := by
  induction bundle generalizing m with
  | nil =>
      exact CPOG.Closure.RTC.refl m
  | cons d ds ih =>
      rcases hjoint with ⟨hadm, hrest⟩
      have hstep : MaxStep extend admissible m (extend m d) :=
        ⟨d, hadm, rfl⟩
      have hfirst :
          CPOG.Closure.RTC (MaxStep extend admissible) m (extend m d) :=
        CPOG.Closure.step_to_rtc hstep
      have htail :
          CPOG.Closure.RTC (MaxStep extend admissible)
            (extend m d) (applyBundle extend (extend m d) ds) :=
        ih (m := extend m d) hrest
      exact CPOG.Closure.rtc_trans hfirst htail

/-! ## A.4 Core modal firewall -/

open CPOG.ModalPreservation

def LiftCoreRel
    {WC : Type uW} {WM : Type uV}
    (ι : WC → WM) (R : WC → WC → Prop) : WM → WM → Prop :=
  fun x y => ∃ a b, ι a = x ∧ ι b = y ∧ R a b

def firewallModel
    {WC : Type uW} {WM : Type uV} {Atom : Type uAtom}
    (M : Model WC Atom) (ι : WC → WM)
    (maxVal : WM → Atom → Prop) : Model WM Atom where
  G := LiftCoreRel ι M.G
  D := LiftCoreRel ι M.D
  H := LiftCoreRel ι M.H
  val := maxVal

theorem coreEmbedding_boundedMorphism
    {WC : Type uW} {WM : Type uV} {Atom : Type uAtom}
    (M : Model WC Atom) (ι : WC → WM)
    (maxVal : WM → Atom → Prop)
    (hinj : Function.Injective ι)
    (hval : ∀ w a, M.val w a ↔ maxVal (ι w) a) :
    BoundedMorphism M (firewallModel M ι maxVal) ι := by
  refine {
    atom := hval
    forthG := ?_
    backG := ?_
    forthD := ?_
    backD := ?_
    forthH := ?_
    backH := ?_
  }
  · intro x y hxy
    exact ⟨x, y, rfl, rfl, hxy⟩
  · intro x z hxz
    rcases hxz with ⟨a, b, ha, hb, hab⟩
    have hax : a = x := hinj ha
    subst a
    exact ⟨b, hab, hb⟩
  · intro x y hxy
    exact ⟨x, y, rfl, rfl, hxy⟩
  · intro x z hxz
    rcases hxz with ⟨a, b, ha, hb, hab⟩
    have hax : a = x := hinj ha
    subst a
    exact ⟨b, hab, hb⟩
  · intro x y hxy
    exact ⟨x, y, rfl, rfl, hxy⟩
  · intro x z hxz
    rcases hxz with ⟨a, b, ha, hb, hab⟩
    have hax : a = x := hinj ha
    subst a
    exact ⟨b, hab, hb⟩

/--
Core formulas have exactly the same truth value after embedding into the
firewalled Core-view of Max. Extra Max stages are invisible to Core modalities.
-/
theorem modalFirewall_satisfaction
    {WC : Type uW} {WM : Type uV} {Atom : Type uAtom}
    (M : Model WC Atom) (ι : WC → WM)
    (maxVal : WM → Atom → Prop)
    (hinj : Function.Injective ι)
    (hval : ∀ w a, M.val w a ↔ maxVal (ι w) a)
    (φ : Formula Atom) (w : WC) :
    Sat M w φ ↔ Sat (firewallModel M ι maxVal) (ι w) φ := by
  exact sat_iff_of_boundedMorphism
    (coreEmbedding_boundedMorphism M ι maxVal hinj hval) φ w

end CPOG.MaxAppendix
