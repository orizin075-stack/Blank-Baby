namespace CPOG
namespace SubmissionCore

/-!
# v57 reviewer-facing theorem core

The central results are now exact characterizations.

* SC3: on reflexive-transitive generation frames, persistent exclusive
  branching exists exactly when universal .2 fails at the root.
* SC5: universal Subsumption is exactly forward invariance of acceptance.
* SC6: equivalently, universal Subsumption is exactly the condition that the
  acceptance predicate is fixed by both canonical stabilization operators.

Thus modal divergence, evaluation stability, and canonical repair are expressed
in a single invariant-region framework.
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

/--
SC3. Exact irreversible-branching characterization.
On every reflexive-transitive frame, two reachable mutually exclusive
forward-invariant regions exist iff universal .2 fails at the root.
-/
theorem persistentBranchSplitIffDot2Failure
    {W : Type u} (R : Rel W) {r : W}
    (hRefl : Reflexive R)
    (hTrans : Transitive R) :
    PersistentBranchSplitAt R r <->
      Not (Dot2ValidAt R r) :=
  persistentBranchSplit_iff_dot2Failure R hRefl hTrans

/--
SC4. Same model and same bisimulation-safe quotient:
the independent-order root becomes directed and validates .2 for all
valuations after abstraction, while the FirstCommit root still refutes .2.
-/
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
SC5. Generic preservation characterization.
For every summary-state carrier, arbitrary admissible update relation and
acceptance predicate, universal G-over-D Subsumption is equivalent to forward
invariance of the acceptance region.
-/
theorem universalSubsumptionIffForwardInvariant
    {S : Type u} (G : StateGrowth S) (A : S -> Prop) :
    UniversalStateSubsumption G A <->
      ForwardInvariantRegion G.rel A :=
  universal_state_subsumption_iff_forwardInvariant G A

/--
SC6. Canonical fixed-point characterization.
Universal Subsumption holds exactly when the acceptance predicate is fixed by
both the least invariant expansion (ForwardClosure) and the greatest invariant
contraction (InvariantKernel).
-/
theorem universalSubsumptionIffCanonicalFixedPoint
    {S : Type u} (G : StateGrowth S) (A : S -> Prop) :
    UniversalStateSubsumption G A <->
      (PredEq (ForwardClosure G.rel A) A /\
       PredEq (InvariantKernel G.rel A) A) :=
  universalSubsumption_iff_canonical_fixed_point G A

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
