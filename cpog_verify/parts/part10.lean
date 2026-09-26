namespace CPOG

/-!
# Max formal core

This section formalizes the Max design conditions that were previously only
stated as an appendix program: free atomic extension, freshness/non-leaf,
finite processing closure for seal completion, prefix-admissible finite
realization, record round-trip, and modal-firewall conservativity.
-/

universe u v w

/-! ## Free atomic extension and initiality -/

structure AtomicExtension (Base : Type u) where
  Carrier : Type u
  base : Base -> Carrier
  fresh : Carrier

def AtomicHom {Base : Type u}
    (A B : AtomicExtension Base) : Type u :=
  { f : A.Carrier -> B.Carrier //
      (forall b, f (A.base b) = B.base b) /\ f A.fresh = B.fresh }

def StandardAtomicExtension (Base : Type u) : AtomicExtension Base where
  Carrier := Sum Base Unit
  base := Sum.inl
  fresh := Sum.inr ()

def standardAtomicHom {Base : Type u} (X : AtomicExtension Base) :
    AtomicHom (StandardAtomicExtension Base) X := by
  refine ⟨?_, ?_, ?_⟩
  · intro x
    cases x with
    | inl b => exact X.base b
    | inr _ => exact X.fresh
  · intro b
    rfl
  · rfl

theorem standardAtomicHom_unique
    {Base : Type u} (X : AtomicExtension Base)
    (f : AtomicHom (StandardAtomicExtension Base) X) :
    f = standardAtomicHom X := by
  apply Subtype.ext
  funext x
  cases x with
  | inl b =>
      exact f.2.1 b
  | inr z =>
      cases z
      exact f.2.2

theorem standard_atomic_initial
    {Base : Type u} (X : AtomicExtension Base) :
    ∃! f : AtomicHom (StandardAtomicExtension Base) X, True := by
  refine ⟨standardAtomicHom X, trivial, ?_⟩
  intro f _
  exact standardAtomicHom_unique X f

theorem standard_atomic_freshness
    {Base : Type u} (b : Base) :
    (StandardAtomicExtension Base).fresh !=
      (StandardAtomicExtension Base).base b := by
  intro h
  cases h

/-! ## Round-trip record conservativity -/

structure CoreRecord (Data : Type u) where
  data : Data

structure MaxRecord (Data : Type u) (Extra : Type v) where
  core : CoreRecord Data
  extra : Extra

def extendRecord {Data : Type u} {Extra : Type v}
    (r : CoreRecord Data) (x : Extra) : MaxRecord Data Extra :=
  ⟨r, x⟩

def forgetRecord {Data : Type u} {Extra : Type v}
    (r : MaxRecord Data Extra) : CoreRecord Data :=
  r.core

theorem forget_extend_record
    {Data : Type u} {Extra : Type v}
    (r : CoreRecord Data) (x : Extra) :
    forgetRecord (extendRecord r x) = r := by
  rfl

/-! ## Fresh providers and the Max non-leaf property -/

structure FreshProvider (Desc : Type u) where
  fresh : List Desc -> Desc
  fresh_not_mem : forall s, fresh s ∉ s

def FreshStep {Desc : Type u} (F : FreshProvider Desc) :
    Rel (List Desc) :=
  fun s t => t = s ++ [F.fresh s]

theorem max_non_leaf
    {Desc : Type u} (F : FreshProvider Desc) (s : List Desc) :
    exists t, FreshStep F s t /\ t ≠ s := by
  refine ⟨s ++ [F.fresh s], rfl, ?_⟩
  intro hEq
  have hLen := congrArg List.length hEq
  simp at hLen

theorem max_fresh_descriptor_not_already_present
    {Desc : Type u} (F : FreshProvider Desc) (s : List Desc) :
    F.fresh s ∉ s :=
  F.fresh_not_mem s

/-! ## Why finite seed is insufficient for seal termination -/

def SuccDescriptorStep : Rel Nat :=
  fun x y => y = x + 1

theorem succ_descriptor_reachable_from_zero :
    forall n : Nat, RTC SuccDescriptorStep 0 n := by
  intro n
  induction n with
  | zero =>
      exact RTC.refl 0
  | succ n ih =>
      exact RTC.tail ih (by simp [SuccDescriptorStep])

theorem finite_seed_does_not_imply_finite_processing_closure :
    forall k : Nat, exists d : Nat,
      RTC SuccDescriptorStep 0 d /\ k < d := by
  intro k
  exact ⟨k + 1, succ_descriptor_reachable_from_zero (k + 1),
    Nat.lt_succ_self k⟩

/-! ## Finite processing closure and seal completion -/

structure FiniteProcessingClosure (Desc : Type u) where
  count : Nat
  descriptor : Fin count -> Desc
  generates : Fin count -> Fin count -> Prop

def ProcessedAfter {Desc : Type u}
    (C : FiniteProcessingClosure Desc) (k : Nat) (i : Fin C.count) : Prop :=
  i.val < k

def SealComplete {Desc : Type u}
    (C : FiniteProcessingClosure Desc) : Prop :=
  forall i, ProcessedAfter C C.count i

theorem finite_processing_closure_seals
    {Desc : Type u} (C : FiniteProcessingClosure Desc) :
    SealComplete C := by
  intro i
  exact i.isLt

theorem generated_descriptors_stay_inside_closure
    {Desc : Type u} (C : FiniteProcessingClosure Desc)
    {i j : Fin C.count} (h : C.generates i j) :
    exists k : Fin C.count, k = j := by
  exact ⟨j, rfl⟩

/-! ## Prefix admissibility and finite realization -/

def PrefixAdmissible {Desc : Type u}
    (admissible : List Desc -> Desc -> Prop) :
    List Desc -> List Desc -> Prop
  | _, [] => True
  | base, d :: ds =>
      admissible base d /\
      PrefixAdmissible admissible (base ++ [d]) ds

def MaxStep {Desc : Type u}
    (admissible : List Desc -> Desc -> Prop) :
    Rel (List Desc) :=
  fun s t => exists d, admissible s d /\ t = s ++ [d]

theorem prefix_admissible_realizable
    {Desc : Type u}
    (admissible : List Desc -> Desc -> Prop) :
    forall (base batch : List Desc),
      PrefixAdmissible admissible base batch ->
      RTC (MaxStep admissible) base (base ++ batch) := by
  intro base batch h
  induction batch generalizing base with
  | nil =>
      simpa using (RTC.refl base : RTC (MaxStep admissible) base base)
  | cons d ds ih =>
      rcases h with ⟨hAd, hRest⟩
      have hOne : RTC (MaxStep admissible) base (base ++ [d]) :=
        RTC.tail (RTC.refl base) ⟨d, hAd, rfl⟩
      have hTail :
          RTC (MaxStep admissible) (base ++ [d])
            ((base ++ [d]) ++ ds) :=
        ih (base := base ++ [d]) hRest
      have hAll :
          RTC (MaxStep admissible) base ((base ++ [d]) ++ ds) :=
        RTC.trans hOne hTail
      simpa [List.append_assoc] using hAll

def SameSupport {Desc : Type u} (xs ys : List Desc) : Prop :=
  forall d, d ∈ xs <-> d ∈ ys

def JointlyAdmissible {Desc : Type u}
    (admissible : List Desc -> Desc -> Prop)
    (base batch : List Desc) : Prop :=
  exists order,
    SameSupport order batch /\
    PrefixAdmissible admissible base order

theorem finite_universal_realization
    {Desc : Type u}
    (admissible : List Desc -> Desc -> Prop)
    (base batch : List Desc)
    (h : JointlyAdmissible admissible base batch) :
    exists order,
      SameSupport order batch /\
      RTC (MaxStep admissible) base (base ++ order) := by
  rcases h with ⟨order, hSupport, hPrefix⟩
  exact ⟨order, hSupport,
    prefix_admissible_realizable admissible base order hPrefix⟩

/-! ## Modal firewall -/

structure ModalFirewall
    {CoreWorld : Type u} {Atom : Type w}
    (C : Model CoreWorld Atom) (MaxWorld : Type v) where
  embed : CoreWorld -> MaxWorld
  injective : Function.Injective embed
  valM : MaxWorld -> Atom -> Prop
  rGM : Rel MaxWorld
  rDM : Rel MaxWorld
  rHM : Rel MaxWorld
  atom_preserve :
    forall x a, C.val x a <-> valM (embed x) a
  forthG :
    forall {x x'}, C.rG x x' -> rGM (embed x) (embed x')
  backG :
    forall {x y}, rGM (embed x) y ->
      exists x', C.rG x x' /\ embed x' = y
  forthD :
    forall {x x'}, C.rD x x' -> rDM (embed x) (embed x')
  backD :
    forall {x y}, rDM (embed x) y ->
      exists x', C.rD x x' /\ embed x' = y
  forthH :
    forall {x x'}, C.rH x x' -> rHM (embed x) (embed x')
  backH :
    forall {x y}, rHM (embed x) y ->
      exists x', C.rH x x' /\ embed x' = y

def ModalFirewall.maxModel
    {CoreWorld : Type u} {Atom : Type w}
    {C : Model CoreWorld Atom} {MaxWorld : Type v}
    (F : ModalFirewall C MaxWorld) :
    Model MaxWorld Atom where
  val := F.valM
  rG := F.rGM
  rD := F.rDM
  rH := F.rHM

def FirewallRel
    {CoreWorld : Type u} {Atom : Type w}
    {C : Model CoreWorld Atom} {MaxWorld : Type v}
    (F : ModalFirewall C MaxWorld) :
    CoreWorld -> MaxWorld -> Prop :=
  fun x y => F.embed x = y

theorem firewall_is_bisimulation
    {CoreWorld : Type u} {Atom : Type w}
    {C : Model CoreWorld Atom} {MaxWorld : Type v}
    (F : ModalFirewall C MaxWorld) :
    IsBisimulation C F.maxModel (FirewallRel F) := by
  constructor
  · intro x y hxy a
    subst y
    exact F.atom_preserve x a
  · intro x y hxy x' hxx'
    subst y
    exact ⟨F.embed x', F.forthG hxx', rfl⟩
  · intro x y hxy y' hyy'
    subst y
    rcases F.backG hyy' with ⟨x', hxx', hx'y'⟩
    exact ⟨x', hxx', hx'y'⟩
  · intro x y hxy x' hxx'
    subst y
    exact ⟨F.embed x', F.forthD hxx', rfl⟩
  · intro x y hxy y' hyy'
    subst y
    rcases F.backD hyy' with ⟨x', hxx', hx'y'⟩
    exact ⟨x', hxx', hx'y'⟩
  · intro x y hxy x' hxx'
    subst y
    exact ⟨F.embed x', F.forthH hxx', rfl⟩
  · intro x y hxy y' hyy'
    subst y
    rcases F.backH hyy' with ⟨x', hxx', hx'y'⟩
    exact ⟨x', hxx', hx'y'⟩

theorem modal_firewall_satisfaction
    {CoreWorld : Type u} {Atom : Type w}
    {C : Model CoreWorld Atom} {MaxWorld : Type v}
    (F : ModalFirewall C MaxWorld)
    (phi : Formula Atom) (x : CoreWorld) :
    Satisfies C x phi <->
      Satisfies F.maxModel (F.embed x) phi := by
  exact bisimulation_invariance (firewall_is_bisimulation F) phi rfl

theorem max_extension_core_conservative
    {CoreWorld : Type u} {Atom : Type w}
    {C : Model CoreWorld Atom} {MaxWorld : Type v}
    (F : ModalFirewall C MaxWorld) :
    forall (phi : Formula Atom) (x : CoreWorld),
      Satisfies C x phi <->
        Satisfies F.maxModel (F.embed x) phi := by
  intro phi x
  exact modal_firewall_satisfaction F phi x

structure SealedMaxExtension
    {CoreWorld : Type u} {Atom : Type w}
    (C : Model CoreWorld Atom) (MaxWorld : Type v) (Desc : Type u) where
  firewall : ModalFirewall C MaxWorld
  closure : FiniteProcessingClosure Desc

theorem sealed_max_completion_and_conservativity
    {CoreWorld : Type u} {Atom : Type w}
    {C : Model CoreWorld Atom} {MaxWorld : Type v} {Desc : Type u}
    (E : SealedMaxExtension C MaxWorld Desc) :
    SealComplete E.closure /\
    forall (phi : Formula Atom) (x : CoreWorld),
      Satisfies C x phi <->
        Satisfies E.firewall.maxModel (E.firewall.embed x) phi := by
  constructor
  · exact finite_processing_closure_seals E.closure
  · intro phi x
    exact modal_firewall_satisfaction E.firewall phi x

end CPOG
