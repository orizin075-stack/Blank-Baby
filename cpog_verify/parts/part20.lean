namespace CPOG
namespace SubmissionCore

/-!
# v55 reviewer-facing theorem core

SC5-SC6 are now the generic state-growth representation theorem and its
failure/defeasibility dual.  The v54 four-valued Evidence theorem is a verified
instance via v54_subsumption_iff_generic_universal_subsumption.
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
SC5. Generic master representation theorem.
For any summary-state carrier S, any admissible-growth relation G,
and any acceptance predicate A, universal G-over-D Subsumption over every
G-monotone summary dynamics with reflexive D is equivalent to G-upward closure
of A.
-/
theorem universalSubsumptionIffUpperClosed
    {S : Type u} (G : StateGrowth S) (A : S -> Prop) :
    UniversalStateSubsumption G A <-> StateUpperClosed G A :=
  universal_state_subsumption_iff_upperClosed G A

/--
SC6. Generic failure theorem.
Universal Subsumption fails exactly when acceptance is defeasible under the
chosen admissible-growth relation.
-/
theorem universalSubsumptionFailureIffDefeasible
    {S : Type u} (G : StateGrowth S) (A : S -> Prop) :
    Not (UniversalStateSubsumption G A) <-> StateDefeasible G A :=
  universal_state_subsumption_failure_iff_defeasible G A

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
