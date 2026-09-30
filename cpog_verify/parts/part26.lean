namespace CPOG
namespace PaperClaims

/-!
# v57 paper-level formal claim crosswalk

Every theorem below is only an alias/packaging layer over a theorem already
proved in the formal library.  The purpose of this namespace is to give the
paper one stable, auditable entry point whose names map directly to claims in
the manuscript.
-/

universe u v w x

/-- PC1. Local frame correspondence for .2. -/
theorem localDot2FrameCorrespondence
    {W : Type u} {R : Rel W} {w : W} :
    DirectedAt R w <->
      forall p : W -> Prop,
        Dia R (Box R p) w ->
        Box R (Dia R p) w :=
  directedAt_iff_dot2_all

/-- PC2. Historical commitments persist along combined history reachability. -/
theorem historicalPersistence
    {H : Type u} {Event : Type v} {Record : Type w}
    (S : HistorySystem H Event Record)
    {h h' : H} (hr : S.Reach h h') (e : Event) :
    S.committed h e -> S.committed h' e :=
  HistorySystem.historical_persistence S hr e

/-- PC3a. G reachability has the S4 frame conditions. -/
theorem generationS4Frame
    {H : Type u} {Event : Type v} {Record : Type w}
    (S : HistorySystem H Event Record) :
    Reflexive S.GReach /\ Transitive S.GReach :=
  ⟨HistorySystem.gReach_reflexive S,
   HistorySystem.gReach_transitive S⟩

/-- PC3b. D reachability has the S4 frame conditions. -/
theorem determinationS4Frame
    {H : Type u} {Event : Type v} {Record : Type w}
    (S : HistorySystem H Event Record) :
    Reflexive S.DReach /\ Transitive S.DReach :=
  ⟨HistorySystem.dReach_reflexive S,
   HistorySystem.dReach_transitive S⟩

/-- PC3c. Combined H reachability has the S4 frame conditions. -/
theorem combinedHistoryS4Frame
    {H : Type u} {Event : Type v} {Record : Type w}
    (S : HistorySystem H Event Record) :
    Reflexive S.Reach /\ Transitive S.Reach :=
  ⟨HistorySystem.reach_reflexive S,
   HistorySystem.reach_transitive S⟩

/-- PC4. Raw incomparable histories generate an explicit .2 countervaluation. -/
theorem rawHistoryDot2Failure
    {A : Type u}
    {h x y : List A}
    (hhx : rawReach h x) (hhy : rawReach h y)
    (hxy : Not (rawReach x y)) (hyx : Not (rawReach y x)) :
    let p : List A -> Prop := fun z => rawReach x z
    Dia rawReach (Box rawReach p) h /\
      Not (Box rawReach (Dia rawReach p) h) :=
  raw_branching_dot2_countervaluation hhx hhy hxy hyx

/-- PC5. Deferable finite generation validates .2. -/
theorem deferableGenerationDot2
    (n : Nat) (p : FiniteGenState n -> Prop) (S : FiniteGenState n) :
    Dia (@genReach (Fin n)) (Box (@genReach (Fin n)) p) S ->
    Box (@genReach (Fin n)) (Dia (@genReach (Fin n)) p) S :=
  finite_deferable_dot2 n p S

/-- PC6. Generic irreversible divergence from incompatible invariant regions. -/
theorem irreversibleDivergence
    {W : Type u}
    (R : Rel W) (P Q : W -> Prop)
    {r a b : W}
    (hP : ForwardInvariantRegion R P)
    (hQ : ForwardInvariantRegion R Q)
    (hDisjoint : MutuallyExclusiveRegions P Q)
    (hra : R r a) (hrb : R r b)
    (ha : P a) (hb : Q b) :
    Dia R (Box R P) r /\
    Not (Box R (Dia R P) r) :=
  persistent_incompatible_branches_dot2_failure
    R P Q hP hQ hDisjoint hra hrb ha hb

/-- PC7. FirstCommit is an exact instance of generic irreversible divergence. -/
theorem firstCommitAsInvariantRegionInstance
    {W : Type u} {Choice : Type v}
    (R : Rel W) (F : W -> Option Choice)
    {r a b : W} {A B : Choice}
    (hPersist : FirstCommitPersistent R F)
    (hAB : A ≠ B)
    (hra : R r a) (hrb : R r b)
    (ha : F a = some A) (hb : F b = some B) :
    Dia R (Box R (FirstCommitPA F A)) r /\
    Not (Box R (Dia R (FirstCommitPA F A)) r) :=
  firstCommit_dot2_failure_is_persistent_region_instance
    R F hPersist hAB hra hrb ha hb

/-- PC8. Same-abstraction modal contrast between deferable and irreversible roots. -/
theorem abstractionModalContrast :
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

/-- PC9. Maximal dynamic bisimilarity is itself dynamically safe. -/
theorem maximalDynamicEquivalence
    {W : Type u} {Atom : Type v}
    (M : Model W Atom) :
    DynamicEquiv M (DynamicBisimilar M) :=
  dynamicBisimilar_dynamicEquiv M

/-- PC10. The maximal dynamic quotient preserves every modal formula. -/
theorem maximalDynamicQuotientTruth
    {W : Type u} {Atom : Type v}
    (M : Model W Atom)
    (phi : Formula Atom) (x : W) :
    Satisfies M x phi <->
      Satisfies
        (quotientModel M (maximalDynamicPresentation M))
        ((maximalDynamicPresentation M).classOf x)
        phi :=
  maximal_dynamic_quotient_truth_preservation M phi x

/-- PC11. Every dynamically safe equivalence refines the maximal quotient. -/
theorem maximalDynamicQuotientCoarsest
    {W : Type u} {Atom : Type v}
    (M : Model W Atom)
    {E : W -> W -> Prop}
    (hE : DynamicEquiv M E) :
    forall {x y},
      E x y ->
      (maximalDynamicPresentation M).classOf x =
        (maximalDynamicPresentation M).classOf y :=
  maximal_dynamic_quotient_is_coarsest M hE

/-- PC12. Static current-atom agreement can fail dynamic safety. -/
theorem staticDynamicGap :
    StaticAtomEq staticDynamicModel .x .y /\
    Not (DynamicBisimilar staticDynamicModel .x .y) :=
  static_observation_not_dynamic_safety_witness

/-- PC13. Origin individuates history without forcing every semantic distinction. -/
theorem originIndividuationSemanticDeflation :
    originWitnessA ≠ originWitnessB /\
    ObsEq payloadOnlyObservation originWitnessA originWitnessB :=
  origin_individuation_semantic_deflation_witness

/-- PC14. Any observation-preserving relation refines semantic observation equality. -/
theorem semanticMinimalQuotient
    {I : Type u} {X : Type v} {Y : Type w}
    (O : I -> X -> Y) (E : X -> X -> Prop)
    (hPres : forall {x y}, E x y -> forall i, O i x = O i y) :
    forall {x y}, E x y -> ObsEq O x y :=
  semantic_minimal_quotient O E hPres

/-- PC15. Historical content Subsumption fails in the canonical history system. -/
theorem historicalSubsumptionFailure :
    Box subHistory.DReach notCommittedInSubHistory .h /\
    Not (Box subHistory.GReach notCommittedInSubHistory .h) :=
  historical_subsumption_failure_in_history_system

/-- PC16. Universal Subsumption is exactly forward invariance. -/
theorem universalSubsumptionRepresentation
    {S : Type u} (G : StateGrowth S) (A : S -> Prop) :
    UniversalStateSubsumption G A <->
      ForwardInvariantRegion G.rel A :=
  universal_state_subsumption_iff_forwardInvariant G A

/-- PC17. Failure is exactly non-invariance. -/
theorem universalSubsumptionFailure
    {S : Type u} (G : StateGrowth S) (A : S -> Prop) :
    Not (UniversalStateSubsumption G A) <->
      Not (ForwardInvariantRegion G.rel A) :=
  universal_state_subsumption_failure_iff_nonInvariant G A

/-- PC18. Two canonical stabilization operators restore universal Subsumption. -/
theorem canonicalStabilization
    {S : Type u} (G : StateGrowth S) (A : S -> Prop) :
    UniversalStateSubsumption G (ForwardClosure G.rel A) /\
    UniversalStateSubsumption G (InvariantKernel G.rel A) :=
  canonical_stabilizations_restore_subsumption G A

/-- PC19. Pure awareness growth with unchanged tracked coordinates is judgment-silent. -/
theorem awarenessSilence
    {W : Type u}
    (V : ViewFn) (S : EvidenceDynamics W)
    {x y : W}
    (hG : S.gR x y)
    (hE : S.evidence x = S.evidence y)
    (hD : S.decision x = S.decision y) :
    S.PosOnly V x <-> S.PosOnly V y :=
  pure_awareness_growth_is_judgment_silent V S hG hE hD

/-- PC20. committed/live/believed possibility roles are formally separable. -/
theorem possibilityRoleSeparation :
    cpogRoleModel.live ≠ cpogRoleModel.believed /\
    cpogRoleModel.committed ≠ cpogRoleModel.believed /\
    cpogRoleModel.committed ≠ cpogRoleModel.live :=
  cpog_role_statuses_distinct

/-- PC21. Epistemic role adequacy does not force metaphysical possibility. -/
theorem metaphysicalBridgeNotForced :
    PossibilityRoleAdequate cpogRoleModel /\
    Not (BridgeToMetaphysical cpogRoleModel roleMetFalse) :=
  role_adequacy_does_not_force_metaphysical_bridge

/-- PC22. A jointly admissible finite Max batch can be realized. -/
theorem finiteMaxRealization
    {Desc : Type u}
    (admissible : List Desc -> Desc -> Prop)
    (base batch : List Desc)
    (h : JointlyAdmissible admissible base batch) :
    exists order,
      SameSupport order batch /\
      RTC (MaxStep admissible) base (base ++ order) :=
  finite_universal_realization admissible base batch h

/-- PC23. A sealed Max extension preserves Core modal truth. -/
theorem maxSealAndConservativity
    {CoreWorld : Type u} {Atom : Type w}
    {C : Model CoreWorld Atom} {MaxWorld : Type v} {Desc : Type u}
    (E : SealedMaxExtension C MaxWorld Desc) :
    SealComplete E.closure /\
    forall (phi : Formula Atom) (x : CoreWorld),
      Satisfies C x phi <->
        Satisfies E.firewall.maxModel (E.firewall.embed x) phi :=
  sealed_max_completion_and_conservativity E


/-- PC24. Incompatible invariant branches force local non-directedness. -/
theorem irreversibleDivergenceNotDirected
    {W : Type u}
    (R : Rel W) (P Q : W -> Prop)
    {r a b : W}
    (hP : ForwardInvariantRegion R P)
    (hQ : ForwardInvariantRegion R Q)
    (hDisjoint : MutuallyExclusiveRegions P Q)
    (hra : R r a) (hrb : R r b)
    (ha : P a) (hb : Q b) :
    Not (DirectedAt R r) :=
  persistent_incompatible_branches_not_directed
    R P Q hP hQ hDisjoint hra hrb ha hb

/-- PC25. ForwardClosure is the least forward-invariant expansion of P. -/
theorem forwardClosureLeast
    {W : Type u} (R : Rel W) (P Q : W -> Prop)
    (hQInv : ForwardInvariantRegion R Q)
    (hPQ : PredSubset P Q) :
    PredSubset (ForwardClosure R P) Q :=
  forwardClosure_least R P Q hQInv hPQ

/-- PC26. InvariantKernel is the greatest forward-invariant contraction of P. -/
theorem invariantKernelGreatest
    {W : Type u} (R : Rel W) (P Q : W -> Prop)
    (hQInv : ForwardInvariantRegion R Q)
    (hQP : PredSubset Q P) :
    PredSubset Q (InvariantKernel R P) :=
  invariantKernel_greatest R P Q hQInv hQP

/-- PC27. Both canonical stabilization operators are idempotent pointwise. -/
theorem canonicalStabilizationIdempotent
    {W : Type u} (R : Rel W) (P : W -> Prop) (x : W) :
    (ForwardClosure R (ForwardClosure R P) x <->
      ForwardClosure R P x) /\
    (InvariantKernel R (InvariantKernel R P) x <->
      InvariantKernel R P x) :=
  ⟨forwardClosure_idempotent_pointwise R P x,
   invariantKernel_idempotent_pointwise R P x⟩

/-- PC28. The canonical two-state content model recovers Subsumption exactly at stability. -/
theorem canonicalContentStableRecovery (V : ViewFn) :
    CanonicalContentSubsumptionHolds V <->
      (V .T .resolvedPos = .T -> V .B .resolvedPos = .T) :=
  content_subsumption_holds_iff_stable V

/-- PC29. The v54 Evidence/Decision representation is an exact instance of the generic master theorem. -/
theorem evidenceDynamicsAsGenericInstance
    (P : EvidencePreorder) (V : ViewFn) :
    UniversalContentSubsumptionBy P V <->
      UniversalStateSubsumption
        (evidenceDecisionGrowth P) (acceptByView V) :=
  v54_subsumption_iff_generic_universal_subsumption P V

/-- PC30. Natural identity evaluation recovers universal Subsumption when growth adds no new negative support. -/
theorem noNewNegativeNaturalRecovery :
    UniversalContentSubsumptionBy
      noNewNegativePreorder identityView :=
  identityView_recovers_noNewNegative_subsumption

end PaperClaims
end CPOG
