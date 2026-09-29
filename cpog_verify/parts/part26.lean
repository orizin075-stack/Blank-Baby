namespace CPOG
namespace PaperClaims

/-!
# v57 paper-level formal theorem crosswalk

This namespace contains only theorem aliases or bundled consequences of the
formal development.  Its purpose is reviewer-facing synchronization: every
major mathematical claim made in the manuscript has a stable Lean name here.

No philosophical uniqueness, empirical adequacy, or interpretive claim is
encoded as a theorem.
-/

/-- PC1. Historical commitment is append-only along combined history reachability. -/
theorem historicalPersistence
    {H : Type u} {Event : Type v} {Record : Type w}
    (S : HistorySystem H Event Record)
    {h h' : H} (hr : S.Reach h h') (e : Event) :
    S.committed h e -> S.committed h' e :=
  HistorySystem.historical_persistence S hr e

/-- PC2. Local frame correspondence for modal .2. -/
theorem localDot2IffDirected
    {W : Type u} {R : Rel W} {w : W} :
    DirectedAt R w <->
      forall p : W -> Prop,
        Dia R (Box R p) w -> Box R (Dia R p) w :=
  directedAt_iff_dot2_all

/-- PC3. Global T correspondence. -/
theorem modalTIffReflexive
    {W : Type u} {R : Rel W} :
    Reflexive R <->
      forall (p : W -> Prop) (w : W), Box R p w -> p w :=
  reflexive_iff_T_all

/-- PC4. Global 4 correspondence. -/
theorem modal4IffTransitive
    {W : Type u} {R : Rel W} :
    Transitive R <->
      forall (p : W -> Prop) (w : W),
        Box R p w -> Box R (Box R p) w :=
  transitive_iff_4_all

/-- PC5. Deferable finite-base generation validates .2. -/
theorem deferableGenerationDot2
    (n : Nat) (p : FiniteGenState n -> Prop) (S : FiniteGenState n) :
    Dia (@genReach (Fin n)) (Box (@genReach (Fin n)) p) S ->
    Box (@genReach (Fin n)) (Dia (@genReach (Fin n)) p) S :=
  finite_deferable_dot2 n p S

/-- PC6. Generic irreversible divergence from disjoint persistent regions. -/
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

/-- PC7. FirstCommit is an exact instance of PC6. -/
theorem firstCommitInstance
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

/-- PC8. Same abstraction: independent .2 recovery and FirstCommit .2 failure. -/
theorem sameAbstractionModalContrast :
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

/-- PC9. Generic Subsumption representation theorem. -/
theorem universalSubsumptionIffForwardInvariant
    {S : Type u} (G : StateGrowth S) (A : S -> Prop) :
    UniversalStateSubsumption G A <->
      ForwardInvariantRegion G.rel A :=
  universal_state_subsumption_iff_forwardInvariant G A

/-- PC10. Generic Subsumption failure is exactly non-invariance. -/
theorem subsumptionFailureIffNonInvariant
    {S : Type u} (G : StateGrowth S) (A : S -> Prop) :
    Not (UniversalStateSubsumption G A) <->
      Not (ForwardInvariantRegion G.rel A) :=
  universal_state_subsumption_failure_iff_nonInvariant G A

/-- PC11. Canonical expansion and contraction repairs both restore Subsumption. -/
theorem canonicalStabilizationRepairs
    {S : Type u} (G : StateGrowth S) (A : S -> Prop) :
    UniversalStateSubsumption G (ForwardClosure G.rel A) /\
    UniversalStateSubsumption G (InvariantKernel G.rel A) :=
  canonical_stabilizations_restore_subsumption G A

/-- PC12. Every chosen DynamicEquiv quotient preserves all G/D/H formulas. -/
theorem dynamicQuotientTruthPreservation
    {W : Type u} {Q : Type v} {Atom : Type w}
    {M : Model W Atom} {E : W -> W -> Prop}
    (hE : DynamicEquiv M E)
    (P : QuotientPresentation W Q E)
    (phi : Formula Atom) (x : W) :
    Satisfies M x phi <->
      Satisfies (quotientModel M P) (P.classOf x) phi :=
  quotient_invariance hE P phi x

/-- PC13. Bisimilarity gives the coarsest DynamicEquiv quotient. -/
theorem coarsestDynamicSafeQuotient
    {W : Type u} {Atom : Type v}
    {M : Model W Atom}
    {E : W -> W -> Prop}
    (hE : DynamicEquiv M E) :
    forall {x y},
      E x y ->
      (bisimilarityPresentation M).classOf x =
        (bisimilarityPresentation M).classOf y :=
  bisimilarity_quotient_is_coarsest_dynamic_safe hE

/-- PC14. The coarsest dynamic-safe quotient preserves modal truth. -/
theorem coarsestDynamicSafeQuotientTruth
    {W : Type u} {Atom : Type v}
    (M : Model W Atom)
    (phi : Formula Atom) (x : W) :
    Satisfies M x phi <->
      Satisfies
        (quotientModel M (bisimilarityPresentation M))
        ((bisimilarityPresentation M).classOf x)
        phi :=
  bisimilarity_quotient_invariance M phi x

/-- PC15. Origin individuation and origin-blind semantic deflation coexist. -/
theorem originIndividuationSemanticDeflation
    {EventCode : Type u} {Payload : Type v}
    {t1 t2 : HistToken EventCode Payload}
    (hOrigin : t1.origin ≠ t2.origin)
    (hPayload : t1.payload = t2.payload) :
    t1 ≠ t2 /\
    ObsEq PayloadObservation t1 t2 :=
  origin_individuation_with_semantic_deflation hOrigin hPayload

/-- PC16. Static observation equivalence is weaker than dynamic safety. -/
theorem staticDynamicGap :
    ObsEq staticAtomObservation
      StaticGapWorld.left StaticGapWorld.right /\
    Not (Bisimilar staticGapModel
      StaticGapWorld.left StaticGapWorld.right) :=
  static_observation_equivalence_not_dynamic_safety

/-- PC17. Observation-preserving identifications refine static observation equality. -/
theorem semanticObservationMinimality
    {I : Type u} {X : Type v} {Y : Type w}
    (O : I -> X -> Y) (E : X -> X -> Prop)
    (hPres : forall {x y}, E x y -> forall i, O i x = O i y) :
    forall {x y}, E x y -> ObsEq O x y :=
  observation_preserving_relation_refines_obsEq O E hPres

/-- PC18. Awareness-silent tracked coordinates preserve every extensional view. -/
theorem awarenessSilence
    {W : Type u}
    (V : ViewFn) (S : EvidenceDynamics W)
    {x y : W}
    (hE : S.evidence x = S.evidence y)
    (hD : S.decision x = S.decision y) :
    S.PosOnly V x <-> S.PosOnly V y :=
  unchanged_coordinates_preserve_PosOnly V S ⟨hE, hD⟩

/-- PC19. Possibility-role adequacy separates committed/live/believed. -/
theorem possibilityRoleSeparation
    {H : Type u} {Token : Type v}
    (M : PossibilityRoleModel H Token)
    (hAdeq : PossibilityRoleAdequate M) :
    M.live ≠ M.believed /\
    M.committed ≠ M.believed /\
    M.committed ≠ M.live :=
  adequate_statuses_are_pairwise_distinct M hAdeq

/-- PC20. Epistemic role adequacy does not force metaphysical possibility. -/
theorem epistemicRoleDoesNotForceMetaphysical :
    PossibilityRoleAdequate cpogRoleModel /\
    Not (BridgeToMetaphysical cpogRoleModel roleMetFalse) :=
  role_adequacy_does_not_force_metaphysical_bridge

/-- PC21. Finite jointly-admissible Max batches are realizable. -/
theorem finiteMaxRealization
    {Desc : Type u}
    (admissible : List Desc -> Desc -> Prop)
    (base batch : List Desc)
    (h : JointlyAdmissible admissible base batch) :
    exists order,
      SameSupport order batch /\
      RTC (MaxStep admissible) base (base ++ order) :=
  finite_universal_realization admissible base batch h

/-- PC22. Sealed Max completion is conservative for Core modal truth. -/
theorem maxSealAndConservativity
    {CoreWorld : Type u} {Atom : Type w}
    {C : Model CoreWorld Atom} {MaxWorld : Type v} {Desc : Type u}
    (E : SealedMaxExtension C MaxWorld Desc) :
    SealComplete E.closure /\
    forall (phi : Formula Atom) (x : CoreWorld),
      Satisfies C x phi <->
        Satisfies E.firewall.maxModel (E.firewall.embed x) phi :=
  sealed_max_completion_and_conservativity E

end PaperClaims
end CPOG
