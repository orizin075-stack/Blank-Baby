
def PosOnly (w : SubWorld) : Prop := currentView w = .T

theorem decision_state_unchanged : currentDecision .h = currentDecision .g := rfl

theorem g_adds_defeating_evidence :
    currentEvidence .h = .T /\ currentEvidence .g = .B := by
  constructor <;> rfl

theorem derived_view_changes_under_G :
    currentView .h = .T /\ currentView .g = .B := by
  constructor <;> rfl

theorem content_boxD : Box dR PosOnly .h := by
  intro v hv
  cases v with
  | h => rfl
  | g => cases hv

theorem content_not_boxG : Not (Box gR PosOnly .h) := by
  intro hbox
  have hp : PosOnly .g := hbox .g (by trivial)
  unfold PosOnly currentView DecideView currentEvidence currentDecision at hp
  cases hp

theorem defeasible_content_subsumption_failure :
    Box dR PosOnly .h /\ Not (Box gR PosOnly .h) :=
  ⟨content_boxD, content_not_boxG⟩

end CPOG


namespace CPOG

universe u v w

inductive Formula (Atom : Type u) where
  | atom : Atom -> Formula Atom
  | top : Formula Atom
  | bot : Formula Atom
  | neg : Formula Atom -> Formula Atom
  | and : Formula Atom -> Formula Atom -> Formula Atom
  | or : Formula Atom -> Formula Atom -> Formula Atom
  | boxG : Formula Atom -> Formula Atom
  | boxD : Formula Atom -> Formula Atom
  | boxH : Formula Atom -> Formula Atom
  | diaG : Formula Atom -> Formula Atom
  | diaD : Formula Atom -> Formula Atom
  | diaH : Formula Atom -> Formula Atom

structure Model (W : Type u) (Atom : Type v) where
  val : W -> Atom -> Prop
  rG : Rel W
  rD : Rel W
  rH : Rel W

def Satisfies (M : Model W Atom) : W -> Formula Atom -> Prop
  | w, .atom a => M.val w a
  | _, .top => True
  | _, .bot => False
  | w, .neg phi => Not (Satisfies M w phi)
  | w, .and phi psi => Satisfies M w phi /\ Satisfies M w psi
  | w, .or phi psi => Satisfies M w phi \/ Satisfies M w psi
  | w, .boxG phi => forall v, M.rG w v -> Satisfies M v phi
  | w, .boxD phi => forall v, M.rD w v -> Satisfies M v phi
  | w, .boxH phi => forall v, M.rH w v -> Satisfies M v phi
  | w, .diaG phi => exists v, M.rG w v /\ Satisfies M v phi
  | w, .diaD phi => exists v, M.rD w v /\ Satisfies M v phi
  | w, .diaH phi => exists v, M.rH w v /\ Satisfies M v phi

structure IsBisimulation
    {W1 : Type u} {W2 : Type v} {Atom : Type w}
    (M1 : Model W1 Atom) (M2 : Model W2 Atom)
    (Z : W1 -> W2 -> Prop) : Prop where
  atom : forall {x y}, Z x y -> forall a, M1.val x a <-> M2.val y a
  forthG : forall {x y}, Z x y -> forall {x'}, M1.rG x x' ->
    exists y', M2.rG y y' /\ Z x' y'
  backG : forall {x y}, Z x y -> forall {y'}, M2.rG y y' ->
    exists x', M1.rG x x' /\ Z x' y'
  forthD : forall {x y}, Z x y -> forall {x'}, M1.rD x x' ->
    exists y', M2.rD y y' /\ Z x' y'
  backD : forall {x y}, Z x y -> forall {y'}, M2.rD y y' ->
    exists x', M1.rD x x' /\ Z x' y'
  forthH : forall {x y}, Z x y -> forall {x'}, M1.rH x x' ->
    exists y', M2.rH y y' /\ Z x' y'
  backH : forall {x y}, Z x y -> forall {y'}, M2.rH y y' ->
    exists x', M1.rH x x' /\ Z x' y'

variable {W1 : Type u} {W2 : Type v} {Atom : Type w}

theorem bisimulation_invariance
    {M1 : Model W1 Atom} {M2 : Model W2 Atom}
    {Z : W1 -> W2 -> Prop} (hZ : IsBisimulation M1 M2 Z) :
    forall (phi : Formula Atom) {x : W1} {y : W2},
      Z x y -> (Satisfies M1 x phi <-> Satisfies M2 y phi) := by
  intro phi
  induction phi with
  | atom a =>
      intro x y hxy
      exact hZ.atom hxy a
  | top =>
      intro x y hxy
      constructor <;> intro h <;> trivial
  | bot =>
      intro x y hxy
      constructor <;> intro h <;> cases h
  | neg phi ih =>
      intro x y hxy
      constructor
      · intro hn hy
        exact hn ((ih hxy).mpr hy)
      · intro hn hx
        exact hn ((ih hxy).mp hx)
  | and phi psi ihPhi ihPsi =>
      intro x y hxy
      constructor
      · intro h
        exact ⟨(ihPhi hxy).mp h.1, (ihPsi hxy).mp h.2⟩
      · intro h
        exact ⟨(ihPhi hxy).mpr h.1, (ihPsi hxy).mpr h.2⟩
  | or phi psi ihPhi ihPsi =>
      intro x y hxy
      constructor
      · intro h
        cases h with
        | inl hp => exact Or.inl ((ihPhi hxy).mp hp)
        | inr hp => exact Or.inr ((ihPsi hxy).mp hp)
      · intro h
        cases h with
        | inl hp => exact Or.inl ((ihPhi hxy).mpr hp)
        | inr hp => exact Or.inr ((ihPsi hxy).mpr hp)
  | boxG phi ih =>
      intro x y hxy
      constructor
      · intro hx y' hyy'
        rcases hZ.backG hxy hyy' with ⟨x', hxx', hx'y'⟩
        exact (ih hx'y').mp (hx x' hxx')
      · intro hy x' hxx'
        rcases hZ.forthG hxy hxx' with ⟨y', hyy', hx'y'⟩
        exact (ih hx'y').mpr (hy y' hyy')
  | boxD phi ih =>
      intro x y hxy
      constructor
      · intro hx y' hyy'
        rcases hZ.backD hxy hyy' with ⟨x', hxx', hx'y'⟩
        exact (ih hx'y').mp (hx x' hxx')
      · intro hy x' hxx'
        rcases hZ.forthD hxy hxx' with ⟨y', hyy', hx'y'⟩
        exact (ih hx'y').mpr (hy y' hyy')
  | boxH phi ih =>
      intro x y hxy
      constructor
      · intro hx y' hyy'
        rcases hZ.backH hxy hyy' with ⟨x', hxx', hx'y'⟩
        exact (ih hx'y').mp (hx x' hxx')
      · intro hy x' hxx'
        rcases hZ.forthH hxy hxx' with ⟨y', hyy', hx'y'⟩
        exact (ih hx'y').mpr (hy y' hyy')
  | diaG phi ih =>
      intro x y hxy
      constructor
      · intro hx
        rcases hx with ⟨x', hxx', hphi⟩
        rcases hZ.forthG hxy hxx' with ⟨y', hyy', hx'y'⟩
        exact ⟨y', hyy', (ih hx'y').mp hphi⟩
      · intro hy
        rcases hy with ⟨y', hyy', hphi⟩
        rcases hZ.backG hxy hyy' with ⟨x', hxx', hx'y'⟩
        exact ⟨x', hxx', (ih hx'y').mpr hphi⟩
  | diaD phi ih =>
      intro x y hxy
      constructor
      · intro hx
        rcases hx with ⟨x', hxx', hphi⟩
        rcases hZ.forthD hxy hxx' with ⟨y', hyy', hx'y'⟩
        exact ⟨y', hyy', (ih hx'y').mp hphi⟩
      · intro hy
        rcases hy with ⟨y', hyy', hphi⟩
        rcases hZ.backD hxy hyy' with ⟨x', hxx', hx'y'⟩
        exact ⟨x', hxx', (ih hx'y').mpr hphi⟩
