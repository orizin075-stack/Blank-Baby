import Std
import CPOGMain
import CPOGTheory
import CPOGOrigin
import CPOGHistory

namespace CPOG.EpistemicPotentialism.Language

inductive Formula (Atom : Type) where
  | atom : Atom → Formula Atom
  | top : Formula Atom
  | bot : Formula Atom
  | neg : Formula Atom → Formula Atom
  | and : Formula Atom → Formula Atom → Formula Atom
  | imp : Formula Atom → Formula Atom → Formula Atom
  | boxG : Formula Atom → Formula Atom
  | diaG : Formula Atom → Formula Atom
  | boxD : Formula Atom → Formula Atom
  | diaD : Formula Atom → Formula Atom
  deriving Repr

open Formula

def Sat {W Atom : Type}
    (RG RD : W → W → Prop) (V : Atom → W → Prop) : W → Formula Atom → Prop
  | w, .atom a => V a w
  | _, .top => True
  | _, .bot => False
  | w, .neg φ => ¬ Sat RG RD V w φ
  | w, .and φ ψ => Sat RG RD V w φ ∧ Sat RG RD V w ψ
  | w, .imp φ ψ => Sat RG RD V w φ → Sat RG RD V w ψ
  | w, .boxG φ => ∀ v, RG w v → Sat RG RD V v φ
  | w, .diaG φ => ∃ v, RG w v ∧ Sat RG RD V v φ
  | w, .boxD φ => ∀ v, RD w v → Sat RG RD V v φ
  | w, .diaD φ => ∃ v, RD w v ∧ Sat RG RD V v φ

def dotTwoFormula {Atom : Type} (p : Atom) : Formula Atom :=
  .imp (.diaG (.boxG (.atom p))) (.boxG (.diaG (.atom p)))

def subsumptionFormula {Atom : Type} (p : Atom) : Formula Atom :=
  .imp (.boxD (.atom p)) (.boxG (.atom p))

theorem sat_dotTwoFormula_iff {W Atom : Type}
    (RG RD : W → W → Prop) (V : Atom → W → Prop) (w : W) (p : Atom) :
    Sat RG RD V w (dotTwoFormula p) ↔ DotTwo RG (V p) w := by
  rfl

theorem sat_subsumptionFormula_iff {W Atom : Type}
    (RG RD : W → W → Prop) (V : Atom → W → Prop) (w : W) (p : Atom) :
    Sat RG RD V w (subsumptionFormula p) ↔ SubsumptionAt RD RG (V p) w := by
  rfl

inductive FirstCommitAtom where
  | firstA
  deriving DecidableEq, Repr

def firstCommitVal : FirstCommitAtom → GWorld → Prop
  | .firstA => firstCommitAProp

theorem firstCommit_formula_dotTwo_fails :
    ¬ Sat firstCommitR firstCommitR firstCommitVal GWorld.root
      (dotTwoFormula FirstCommitAtom.firstA) := by
  intro h
  have hdot : DotTwo firstCommitR firstCommitAProp GWorld.root :=
    (sat_dotTwoFormula_iff firstCommitR firstCommitR firstCommitVal GWorld.root
      FirstCommitAtom.firstA).1 h
  exact firstCommit_relation_dotTwo_fails hdot

inductive HistoricalAtom where
  | uncommittedC
  deriving DecidableEq, Repr

def historicalVal : HistoricalAtom → HDWorld → Prop
  | .uncommittedC => notCommittedCProp

theorem historical_formula_subsumption_fails :
    ¬ Sat gRHD dR historicalVal HDWorld.now
      (subsumptionFormula HistoricalAtom.uncommittedC) := by
  intro h
  have hsub : SubsumptionAt dR gRHD notCommittedCProp HDWorld.now :=
    (sat_subsumptionFormula_iff gRHD dR historicalVal HDWorld.now
      HistoricalAtom.uncommittedC).1 h
  exact historical_relation_subsumption_fails hsub

inductive ContentAtom where
  | positive
  deriving DecidableEq, Repr

def contentVal : ContentAtom → Theory.ContentWorld → Prop
  | .positive => Theory.ContentPositive

theorem content_formula_subsumption_fails :
    ¬ Sat Theory.GContent Theory.DContent contentVal Theory.ContentWorld.now
      (subsumptionFormula ContentAtom.positive) := by
  intro h
  have hsub : SubsumptionAt Theory.DContent Theory.GContent Theory.ContentPositive
      Theory.ContentWorld.now :=
    (sat_subsumptionFormula_iff Theory.GContent Theory.DContent contentVal
      Theory.ContentWorld.now ContentAtom.positive).1 h
  have htheory : ¬ Theory.SubsumptionAt Theory.DContent Theory.GContent
      Theory.ContentPositive Theory.ContentWorld.now := Theory.content_subsumption_fails
  exact htheory hsub

theorem firstCommit_abstraction_formula_dotTwo_fails
    {W Q A : Type} {R : W → W → Prop} {q : W → Q} {lab : W → Option A}
    {root xA xB : W} {a b : A}
    (hpersist : Theory.LabelPersistent R lab)
    (hpres : Theory.AbstractionPreservesLabel q lab)
    (hrootA : R root xA)
    (hrootB : R root xB)
    (hA : lab xA = some a)
    (hB : lab xB = some b)
    (hab : a ≠ b) :
    ¬ Sat (Theory.AbstractRel R q) (Theory.AbstractRel R q)
      (fun (_ : Unit) => Theory.AbstractHasLabel q lab a)
      (q root) (dotTwoFormula ()) := by
  intro hSat
  have hDot : Theory.DotTwoAt (Theory.AbstractRel R q)
      (Theory.AbstractHasLabel q lab a) (q root) := by
    exact hSat
  exact Theory.firstCommit_abstraction_dotTwo_fails
    hpersist hpres hrootA hrootB hA hB hab hDot

theorem commutative_formula_dotTwo_valid
    (Atom : Type) (V : Atom → CommState → Prop) (p : Atom) (w : CommState) :
    Sat commR commR V w (dotTwoFormula p) := by
  exact (sat_dotTwoFormula_iff commR commR V w p).2
    (commutative_abstraction_validates_dotTwo (V p) w)

end CPOG.EpistemicPotentialism.Language
