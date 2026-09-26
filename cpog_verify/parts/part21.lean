namespace CPOG

/-!
# Persistent-separator theorem

FirstCommit is one mechanism that creates persistent incompatible regions.
The modal obstruction itself is more general: whenever two incompatible
predicates are both reachable from one root and each is forward-persistent,
.2 fails for either predicate against the other branch.
-/

def ForwardPersistent
    {W : Type u} (R : Rel W) (P : W -> Prop) : Prop :=
  forall {x y : W}, R x y -> P x -> P y

def IncompatiblePredicates
    {W : Type u} (P Q : W -> Prop) : Prop :=
  forall x : W, P x -> Q x -> False

theorem persistent_incompatible_branches_refute_dot2
    {W : Type u}
    (R : Rel W) (P Q : W -> Prop)
    {r p q : W}
    (hP : ForwardPersistent R P)
    (hQ : ForwardPersistent R Q)
    (hIncompat : IncompatiblePredicates P Q)
    (hrp : R r p) (hrq : R r q)
    (hp : P p) (hq : Q q) :
    Dia R (Box R P) r /\
    Not (Box R (Dia R P) r) := by
  constructor
  · refine ⟨p, hrp, ?_⟩
    intro y hpy
    exact hP hpy hp
  · intro hBox
    rcases hBox q hrq with ⟨y, hqy, hPy⟩
    have hQy : Q y := hQ hqy hq
    exact hIncompat y hPy hQy

theorem firstCommit_predicate_forwardPersistent
    {W : Type u} {Choice : Type v}
    (R : Rel W) (F : W -> Option Choice)
    (hPersist : FirstCommitPersistent R F)
    (A : Choice) :
    ForwardPersistent R (FirstCommitPA F A) := by
  intro x y hxy hx
  exact hPersist hxy hx

theorem distinct_firstCommit_predicates_incompatible
    {W : Type u} {Choice : Type v}
    (F : W -> Option Choice)
    {A B : Choice}
    (hAB : A ≠ B) :
    IncompatiblePredicates
      (FirstCommitPA F A)
      (FirstCommitPA F B) := by
  intro x hA hB
  have hSome : (some A : Option Choice) = some B :=
    Eq.trans hA.symm hB
  exact hAB (Option.some.inj hSome)

theorem firstCommit_dot2_failure_via_persistent_separator
    {W : Type u} {Choice : Type v}
    (R : Rel W) (F : W -> Option Choice)
    {r a b : W} {A B : Choice}
    (hPersist : FirstCommitPersistent R F)
    (hAB : A ≠ B)
    (hra : R r a) (hrb : R r b)
    (ha : F a = some A) (hb : F b = some B) :
    Dia R (Box R (FirstCommitPA F A)) r /\
    Not (Box R (Dia R (FirstCommitPA F A)) r) := by
  exact persistent_incompatible_branches_refute_dot2
    R
    (FirstCommitPA F A)
    (FirstCommitPA F B)
    (firstCommit_predicate_forwardPersistent R F hPersist A)
    (firstCommit_predicate_forwardPersistent R F hPersist B)
    (distinct_firstCommit_predicates_incompatible F hAB)
    hra hrb ha hb

namespace SubmissionCore

theorem generalizedPersistentSeparatorDot2Failure
    {W : Type u}
    (R : Rel W) (P Q : W -> Prop)
    {r p q : W}
    (hP : ForwardPersistent R P)
    (hQ : ForwardPersistent R Q)
    (hIncompat : IncompatiblePredicates P Q)
    (hrp : R r p) (hrq : R r q)
    (hp : P p) (hq : Q q) :
    Dia R (Box R P) r /\
    Not (Box R (Dia R P) r) :=
  persistent_incompatible_branches_refute_dot2
    R P Q hP hQ hIncompat hrp hrq hp hq

end SubmissionCore
end CPOG
