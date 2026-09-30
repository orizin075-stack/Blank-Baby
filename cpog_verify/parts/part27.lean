namespace CPOG
namespace SubmissionCore

/-!
# v58 reviewer-facing theorem core

The ten theorem surface is now organized around exact structural
characterizations rather than witness-only results.

SC3  generic irreversible divergence from incompatible invariant regions.
SC4  exact local frame correspondence for .2.
SC5  universal Subsumption iff forward invariance.
SC6  stabilization adjunction ForwardClosure ⊣ InvariantKernel.
SC7-SC10 retain the delimited Max and possibility-role boundaries.
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
SC3. Generic irreversible divergence.
Any two mutually exclusive forward-invariant regions reachable from one root
refute .2 for the first region.
-/
theorem persistentIncompatibleBranchesDot2Failure
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

/--
SC4. Exact local frame correspondence of .2.
At a root w, .2 is valid for every valuation iff the successor cone at w is
directed.
-/
theorem directedAtIffDot2All
    {W : Type u} {R : Rel W} {w : W} :
    DirectedAt R w <->
      forall p : W -> Prop,
        Dia R (Box R p) w -> Box R (Dia R p) w :=
  directedAt_iff_dot2_all

/--
SC5. Generic preservation representation theorem.
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
SC6. Canonical stabilization adjunction.
ForwardClosure is left adjoint to InvariantKernel on the predicate poset.
-/
theorem stabilizationAdjunction
    {W : Type u} (R : Rel W) (P Q : W -> Prop) :
    PredSubset (ForwardClosure R P) Q <->
      PredSubset P (InvariantKernel R Q) :=
  stabilization_adjunction R P Q

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
