import Std

namespace CPOG.EpistemicPotentialism.History

/--
A minimal Core state. Historical registries record committed events,
generated tokens, and generated internal worlds. Core-0 content is attached
to each event code.
-/
structure CoreState (Event Token World Content : Type) where
  committed : Event → Prop
  tokenExists : Token → Prop
  worldExists : World → Prop
  contentAt : Event → Content

/--
A later state is a Core extension when historical registries only grow and
the Core-0 content of every already committed event is preserved.
-/
def CoreExtends {Event Token World Content : Type}
    (h h' : CoreState Event Token World Content) : Prop :=
  (∀ e, h.committed e → h'.committed e) ∧
  (∀ t, h.tokenExists t → h'.tokenExists t) ∧
  (∀ w, h.worldExists w → h'.worldExists w) ∧
  (∀ e, h.committed e → h'.contentAt e = h.contentAt e)

theorem coreExtends_refl {Event Token World Content : Type}
    (h : CoreState Event Token World Content) :
    CoreExtends h h := by
  constructor
  · intro e he
    exact he
  constructor
  · intro t ht
    exact ht
  constructor
  · intro w hw
    exact hw
  · intro e _
    rfl

theorem coreExtends_trans {Event Token World Content : Type}
    {h₀ h₁ h₂ : CoreState Event Token World Content}
    (h01 : CoreExtends h₀ h₁)
    (h12 : CoreExtends h₁ h₂) :
    CoreExtends h₀ h₂ := by
  rcases h01 with ⟨he01, ht01, hw01, hc01⟩
  rcases h12 with ⟨he12, ht12, hw12, hc12⟩
  constructor
  · intro e he0
    exact he12 e (he01 e he0)
  constructor
  · intro t ht0
    exact ht12 t (ht01 t ht0)
  constructor
  · intro w hw0
    exact hw12 w (hw01 w hw0)
  · intro e he0
    have he1 : h₁.committed e := he01 e he0
    exact (hc12 e he1).trans (hc01 e he0)

theorem historical_event_persistence {Event Token World Content : Type}
    {h h' : CoreState Event Token World Content} {e : Event}
    (hext : CoreExtends h h') (he : h.committed e) :
    h'.committed e :=
  hext.1 e he

theorem historical_token_persistence {Event Token World Content : Type}
    {h h' : CoreState Event Token World Content} {t : Token}
    (hext : CoreExtends h h') (ht : h.tokenExists t) :
    h'.tokenExists t :=
  hext.2.1 t ht

theorem historical_world_persistence {Event Token World Content : Type}
    {h h' : CoreState Event Token World Content} {w : World}
    (hext : CoreExtends h h') (hw : h.worldExists w) :
    h'.worldExists w :=
  hext.2.2.1 w hw

theorem historical_content_persistence {Event Token World Content : Type}
    {h h' : CoreState Event Token World Content} {e : Event}
    (hext : CoreExtends h h') (he : h.committed e) :
    h'.contentAt e = h.contentAt e :=
  hext.2.2.2 e he

theorem historical_persistence {Event Token World Content : Type}
    {h h' : CoreState Event Token World Content}
    (hext : CoreExtends h h') :
    (∀ e, h.committed e → h'.committed e ∧ h'.contentAt e = h.contentAt e) ∧
    (∀ t, h.tokenExists t → h'.tokenExists t) ∧
    (∀ w, h.worldExists w → h'.worldExists w) := by
  constructor
  · intro e he
    exact ⟨historical_event_persistence hext he,
      historical_content_persistence hext he⟩
  constructor
  · intro t ht
    exact historical_token_persistence hext ht
  · intro w hw
    exact historical_world_persistence hext hw

end CPOG.EpistemicPotentialism.History
