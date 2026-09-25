import CPOG.General

namespace CPOG.Possibility

universe uH uC uT uU uP

variable {H : Type uH} {C : Type uC} {T : Type uT}
variable {U : Type uU} {P : Type uP}

/-- Typed possibility-token interface. The code space is fixed; historical existence begins only when committedAt holds. -/
structure TokenSystem (H : Type uH) (C : Type uC) (T : Type uT)
    (U : Type uU) (P : Type uP) where
  origin : T → C
  committedAt : H → C → Prop
  liveAdmissible : H → U → P → T → Prop
  futureAllowed : U → P → H → H → Prop
  closed : H → U → P → T → Prop

def PossHist (S : TokenSystem H C T U P) (h : H) (t : T) : Prop :=
  S.committedAt h (S.origin t)

def PossLive (S : TokenSystem H C T U P)
    (h : H) (u : U) (p : P) (t : T) : Prop :=
  PossHist S h t ∧ S.liveAdmissible h u p t

def PossReach (S : TokenSystem H C T U P)
    (h : H) (u : U) (p : P) (t : T) : Prop :=
  ∃ h', S.futureAllowed u p h h' ∧ PossLive S h' u p t

theorem possLive_implies_hist
    (S : TokenSystem H C T U P) {h : H} {u : U} {p : P} {t : T}
    (hlive : PossLive S h u p t) :
    PossHist S h t :=
  hlive.1

/-- Append-only persistence of historical commitment along a transition relation. -/
def CommitPersistent
    (S : TokenSystem H C T U P) (R : H → H → Prop) : Prop :=
  ∀ ⦃h h'⦄, R h h' → ∀ c, S.committedAt h c → S.committedAt h' c

theorem possHist_persistent
    (S : TokenSystem H C T U P) (R : H → H → Prop)
    (hpersist : CommitPersistent S R)
    {h h' : H} {t : T}
    (hR : R h h') (hhist : PossHist S h t) :
    PossHist S h' t :=
  hpersist hR (S.origin t) hhist

/-- If D preserves Core commitment exactly, historical possibility is invariant under D. -/
def CommitInvariant
    (S : TokenSystem H C T U P) (D : H → H → Prop) : Prop :=
  ∀ ⦃h h'⦄, D h h' → ∀ c, S.committedAt h c ↔ S.committedAt h' c

theorem possHist_D_invariant
    (S : TokenSystem H C T U P) (D : H → H → Prop)
    (hinv : CommitInvariant S D)
    {h h' : H} {t : T}
    (hD : D h h') :
    PossHist S h t ↔ PossHist S h' t :=
  hinv hD (S.origin t)

/-- A closure certificate excludes all future live states reachable under the selected use/policy transition system. -/
def ClosureSound
    (S : TokenSystem H C T U P) : Prop :=
  ∀ ⦃h : H⦄ ⦃u : U⦄ ⦃p : P⦄ ⦃t : T⦄,
    S.closed h u p t →
    ∀ h', S.futureAllowed u p h h' → ¬ PossLive S h' u p t

theorem closed_not_possReach
    (S : TokenSystem H C T U P)
    (hsound : ClosureSound S)
    {h : H} {u : U} {p : P} {t : T}
    (hclosed : S.closed h u p t) :
    ¬ PossReach S h u p t := by
  rintro ⟨h', hfuture, hlive⟩
  exact hsound hclosed h' hfuture hlive

/-- Historical existence does not imply live status when current admissibility fails. -/
theorem hist_not_imply_live_of_not_admissible
    (S : TokenSystem H C T U P)
    {h : H} {u : U} {p : P} {t : T}
    (_hhist : PossHist S h t)
    (hnot : ¬ S.liveAdmissible h u p t) :
    ¬ PossLive S h u p t := by
  intro hlive
  exact hnot hlive.2

/-- Historical existence does not imply future reachability under a sound closure ratchet. -/
theorem hist_not_imply_reach_under_closure
    (S : TokenSystem H C T U P)
    (hsound : ClosureSound S)
    {h : H} {u : U} {p : P} {t : T}
    (_hhist : PossHist S h t)
    (hclosed : S.closed h u p t) :
    ¬ PossReach S h u p t :=
  closed_not_possReach S hsound hclosed

/-- G append-only and D Core-invariant assumptions yield the two historical-stability laws. -/
theorem historical_possibility_stability
    (S : TokenSystem H C T U P)
    (G D : H → H → Prop)
    (hG : CommitPersistent S G)
    (hD : CommitInvariant S D)
    {h hg hd : H} {t : T}
    (hgh : G h hg) (hdh : D h hd) (hhist : PossHist S h t) :
    PossHist S hg t ∧ PossHist S hd t := by
  constructor
  · exact possHist_persistent S G hG hgh hhist
  · exact (possHist_D_invariant S D hD hdh).mp hhist

end CPOG.Possibility
