namespace CPOG
namespace SubmissionCore

/-!
# Reviewer-facing theorem core

This file adds no new philosophical assumptions and no new proof mechanism.
It exposes the small theorem set used by the v50 submission manuscript while
leaving the larger verified library available as supporting infrastructure.
-/

/-- SC1. Historical commitment is persistent along the combined history reachability. -/
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

/--
SC3. In one history system and one bisimulation-safe quotient, raw order
non-convergence is erased while FirstCommit separation and the .2 failure remain.
-/
theorem semanticDivergenceContrast :
    (uRG .root .orderAB /\ uRG .root .orderBA /\
      Not (exists z, uRG .orderAB z /\ uRG .orderBA z)) /\
    (uPresentation.classOf .orderAB = uPresentation.classOf .orderBA) /\
    (uPresentation.classOf .commitA ≠ uPresentation.classOf .commitB) /\
    (Satisfies (quotientModel unifiedModel uPresentation)
        (uPresentation.classOf .root) unifiedAntecedent /\
      Not (Satisfies (quotientModel unifiedModel uPresentation)
        (uPresentation.classOf .root) unifiedConsequent)) :=
  same_system_same_abstraction_contrast

/-- SC4. Content-level Subsumption failure is exactly the defeasibility boundary. -/
theorem subsumptionFailureIffDefeasible (V : ViewFn) :
    CanonicalContentSubsumptionFailure V <-> ResolvedPosDefeasible V :=
  content_subsumption_failure_iff_defeasible V

/-- SC5. Content-level Subsumption is recovered exactly under the canonical stability condition. -/
theorem subsumptionRecoveryIffStable (V : ViewFn) :
    CanonicalContentSubsumptionHolds V <->
      (V .T .resolvedPos = .T -> V .B .resolvedPos = .T) :=
  content_subsumption_holds_iff_stable V

/-- SC6. G/D/H modal truth is invariant under the dynamic bisimulation interface. -/
theorem dynamicBisimulationInvariance
    {W1 : Type u} {W2 : Type v} {Atom : Type w}
    {M1 : Model W1 Atom} {M2 : Model W2 Atom}
    {Z : W1 -> W2 -> Prop}
    (hZ : IsBisimulation M1 M2 Z)
    (phi : Formula Atom) {x : W1} {y : W2} (hxy : Z x y) :
    Satisfies M1 x phi <-> Satisfies M2 y phi :=
  bisimulation_invariance hZ phi hxy

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

/-- SC8. A sealed Max extension both completes and conservatively preserves Core modal truth. -/
theorem maxSealAndConservativity
    {CoreWorld : Type u} {Atom : Type w}
    {C : Model CoreWorld Atom} {MaxWorld : Type v} {Desc : Type u}
    (E : SealedMaxExtension C MaxWorld Desc) :
    SealComplete E.closure /\
    forall (phi : Formula Atom) (x : CoreWorld),
      Satisfies C x phi <->
        Satisfies E.firewall.maxModel (E.firewall.embed x) phi :=
  sealed_max_completion_and_conservativity E

/-- SC9. Under the explicit role-adequacy conditions, committed/live/believed are pairwise distinct. -/
theorem possibilityRoleSeparation
    {H : Type u} {Token : Type v}
    (M : PossibilityRoleModel H Token)
    (hAdeq : PossibilityRoleAdequate M) :
    M.live ≠ M.believed /\
    M.committed ≠ M.believed /\
    M.committed ≠ M.live :=
  adequate_statuses_are_pairwise_distinct M hAdeq

/-- SC10. Possibility-role adequacy alone does not entail metaphysical possibility. -/
theorem epistemicRoleDoesNotForceMetaphysical :
    PossibilityRoleAdequate cpogRoleModel /\
    Not (BridgeToMetaphysical cpogRoleModel roleMetFalse) :=
  role_adequacy_does_not_force_metaphysical_bridge

end SubmissionCore
end CPOG
