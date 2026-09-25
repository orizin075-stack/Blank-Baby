import CPOG.Provenance
import CPOG.DynamicQuotient

namespace CPOG.DynamicObservation

open CPOG.SemanticProvenance
open CPOG.ModalPreservation
open CPOG.DynamicQuotient

universe uI uW uA

/--
A dynamic equivalence together with the requirement that every dynamically
identified pair is also indistinguishable by the selected static observations.
-/
structure ObservationDynamicEquivalence
    {ι : Type uI} {W : Type uW} {Atom : Type uA}
    (M : Model W Atom) (O : ObservationSystem ι W) where
  dyn : DynamicEquivalence M
  respectsObservation :
    forall {x y : W}, dyn.E x y -> ObsEq O x y

/--
The dynamic quotient refines the static semantic quotient:
if two states become equal in the dynamic quotient, then they are also equal
in the observation quotient.
-/
theorem dynamic_quotient_refines_static_quotient
    {ι : Type uI} {W : Type uW} {Atom : Type uA}
    {M : Model W Atom} {O : ObservationSystem ι W}
    (B : ObservationDynamicEquivalence M O)
    {x y : W}
    (hxy : CPOG.DynamicQuotient.quotientMap B.dyn x =
      CPOG.DynamicQuotient.quotientMap B.dyn y) :
    CPOG.SemanticProvenance.quotientMap O x =
      CPOG.SemanticProvenance.quotientMap O y := by
  apply Quotient.sound
  exact B.respectsObservation
    ((CPOG.DynamicQuotient.quotientMap_eq_iff B.dyn x y).1 hxy)

/--
Kernel-refinement form of the same result.
-/
theorem dynamic_kernel_refines_observation_equivalence
    {ι : Type uI} {W : Type uW} {Atom : Type uA}
    {M : Model W Atom} {O : ObservationSystem ι W}
    (B : ObservationDynamicEquivalence M O)
    {x y : W}
    (hxy : CPOG.DynamicQuotient.quotientMap B.dyn x =
      CPOG.DynamicQuotient.quotientMap B.dyn y) :
    ObsEq O x y := by
  exact B.respectsObservation
    ((CPOG.DynamicQuotient.quotientMap_eq_iff B.dyn x y).1 hxy)

/--
The same dynamic quotient also preserves every G/D/H modal formula, because
its canonical quotient map is a bounded morphism.
-/
theorem dynamic_observation_quotient_preserves_modal_truth
    {ι : Type uI} {W : Type uW} {Atom : Type uA}
    {M : Model W Atom} {O : ObservationSystem ι W}
    (B : ObservationDynamicEquivalence M O)
    (phi : Formula Atom) (w : W) :
    Sat M w phi <->
      Sat (CPOG.DynamicQuotient.quotientModel B.dyn)
        (CPOG.DynamicQuotient.quotientMap B.dyn w) phi := by
  exact CPOG.DynamicQuotient.dynamicQuotient_preserves_all_formulas
    B.dyn phi w

/--
Combined theorem: a dynamic observation quotient simultaneously preserves
all selected static observations and all formulas of the G/D/H language.
-/
theorem dynamic_observation_quotient_is_semantically_safe
    {ι : Type uI} {W : Type uW} {Atom : Type uA}
    {M : Model W Atom} {O : ObservationSystem ι W}
    (B : ObservationDynamicEquivalence M O) :
    (forall {x y : W},
      CPOG.DynamicQuotient.quotientMap B.dyn x =
        CPOG.DynamicQuotient.quotientMap B.dyn y ->
      ObsEq O x y) /\
    (forall (phi : Formula Atom) (w : W),
      Sat M w phi <->
        Sat (CPOG.DynamicQuotient.quotientModel B.dyn)
          (CPOG.DynamicQuotient.quotientMap B.dyn w) phi) := by
  constructor
  · intro x y hxy
    exact dynamic_kernel_refines_observation_equivalence B hxy
  · intro phi w
    exact dynamic_observation_quotient_preserves_modal_truth B phi w

end CPOG.DynamicObservation
