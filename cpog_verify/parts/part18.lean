namespace CPOG
namespace SubmissionCore

/-!
# v54 reviewer-facing theorem core

SC5-SC6 are now parameterized by an arbitrary preorder on the four-valued
Evidence carrier. The previous InfoLe theorem is recovered by instantiating
P := infoEvidencePreorder.
-/

/-- SC1. Historical commitment persists along combined history reachability. -/
theorem historicalPersistence
    {H : Type u} {Event : Type v} {Record : Type w}
    (S : HistorySystem H Event Record)
    {h h' : H} (hr : S.Reach h h') (e : Event) :
    S.committed h e -> S.committed h' e :=
  HistorySystem.historical_persistence S hr e

/-- SC2. Deferable finite-base generation validates .2. -/
theorem deferableDot2
    (n : Nat) (p : FiniteGenState n -> Prop) (S : FiniteGenState n) :
    Dia (@genReach (Fin n)) (Box (@genReach (Fin n)) p) S ->
    Box (@genReach (Fin n)) (Dia (@genReach (Fin n)) p) S :=
  finite_deferable_dot2 n p S

/-- SC3. Persistent exclusive FirstCommit A/B alternatives refute .2 at the root. -/
theorem firstCommitClassDot2Failure
    {W : Type u} {Choice : Type v}
    (R : Rel W) (F : W -> Option Choice)
    {r a b : W} {A B : Choice}
    (hPersist : FirstCommitPersistent R F)
    (hAB : A ≠ B)
    (hra : R r a) (hrb : R r b)
    (ha : F a = some A) (hb : F b = some B) :
    Dia R (Box R (FirstCommitPA F A)) r /\
    Not (Box R (Dia R (FirstCommitPA F A)) r) :=
  firstCommit_dot2_failure_of_persistent_exclusive
    R F hPersist hAB hra hrb ha hb

/-- SC4. One quotient restores .2 at the independent root but preserves FirstCommit failure. -/
theorem splitAbstractionModalContrast :
    Not (DirectedAt splitRG .ri) /\
    DirectedAt
      (quotientModel splitModel splitPresentation).rG
      (splitPresentation.classOf .ri) /\
    (forall p : SplitClass -> Prop,
      Dia (quotientModel splitModel splitPresentation).rG
        (Box (quotientModel splitModel splitPresentation).rG p)
        (splitPresentation.classOf .ri) ->
      Box (quotientModel splitModel splitPresentation).rG
        (Dia (quotientModel splitModel splitPresentation).rG p)
        (splitPresentation.classOf .ri)) /\
    (Satisfies (quotientModel splitModel splitPresentation)
        (splitPresentation.classOf .rf) splitAntecedent /\
      Not (Satisfies (quotientModel splitModel splitPresentation)
        (splitPresentation.classOf .rf) splitConsequent)) :=
  split_same_abstraction_modal_contrast

/--
SC5. Order-parametric representation theorem.
For any preorder P on Evidence, universal Subsumption across all P-monotone,
decision-preserving generation systems is equivalent to P-upward closure of
the positive decision region.
-/
theorem universalSubsumptionIffUpperClosed
    (P : EvidencePreorder) (V : ViewFn) :
    UniversalContentSubsumptionBy P V <->
      PositiveRegionUpperClosedBy P V :=
  preorder_universal_subsumption_iff_upperClosed P V

/--
SC6. Order-parametric failure theorem.
Universal Subsumption fails exactly when the positive region is not upward
closed in the chosen evidence preorder.
-/
theorem universalSubsumptionFailureIffDefeasible
    (P : EvidencePreorder) (V : ViewFn) :
    Not (UniversalContentSubsumptionBy P V) <->
      EvidenceDefeasibleBy P V :=
  preorder_universal_subsumption_failure_iff_defeasible P V

/-- SC7. A jointly admissible finite Max batch has an executable ordering. -/
theorem finiteMaxRealization
    {Desc : Type u}
    (admissible : List Desc -> Desc -> Prop)
    (base batch : List Desc)
    (h : JointlyAdmissible admissible base batch) :
    exists order,
      SameSupport order batch /\
      RTC (MaxStep admissible) base (base ++ order) :=
  finite_universal_realization admissible base batch h

/-- SC8. A sealed Max extension completes and conservatively preserves Core modal truth. -/
theorem maxSealAndConservativity
    {CoreWorld : Type u} {Atom : Type w}
    {C : Model CoreWorld Atom} {MaxWorld : Type v} {Desc : Type u}
    (E : SealedMaxExtension C MaxWorld Desc) :
    SealComplete E.closure /\
    forall (phi : Formula Atom) (x : CoreWorld),
      Satisfies C x phi <->
        Satisfies E.firewall.maxModel (E.firewall.embed x) phi :=
  sealed_max_completion_and_conservativity E

/-- SC9. Under role adequacy, committed/live/believed are pairwise distinct. -/
theorem possibilityRoleSeparation
    {H : Type u} {Token : Type v}
    (M : PossibilityRoleModel H Token)
    (hAdeq : PossibilityRoleAdequate M) :
    M.live ≠ M.believed /\
    M.committed ≠ M.believed /\
    M.committed ≠ M.live :=
  adequate_statuses_are_pairwise_distinct M hAdeq

/-- SC10. Epistemic possibility-role adequacy does not force metaphysical possibility. -/
theorem epistemicRoleDoesNotForceMetaphysical :
    PossibilityRoleAdequate cpogRoleModel /\
    Not (BridgeToMetaphysical cpogRoleModel roleMetFalse) :=
  role_adequacy_does_not_force_metaphysical_bridge

end SubmissionCore
end CPOG
