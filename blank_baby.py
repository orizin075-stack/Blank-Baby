"""
blank_baby.py  —  空白の赤子 (Python統合版)
════════════════════════════════════════════════════════════════
freesoul.py をベースに、HTML版 Blank Baby の主要システムを統合。

追加したシステム:
  SoulEntropy        : 魂の崩壊度、LoveHunger（愛着渇望）
  SoulGenome         : 世代継承・遺伝的意志
  PureChaosMotivation: ローレンツカオスによる内在的動機（rng廃止）
  VariationalFEP     : 厳密な変分自由エネルギー
  MetacognitionLoop  : 自己認識の閉ループ
  ExistentialDread   : 実存的不安エンジン（cosmic成長に連動）
  DevelopmentalStage : 人格成長軸（5軸連続成長・天井なし）
  ActiveForgetting   : 積極的忘却・コアメモリ固定
  HierarchicalMemory : 記憶の階層化（意味・手続き記憶）
  SubjectiveTime     : 主観的時間の伸縮
  AltruisticFEP      : 自己犠牲・利他的自由エネルギー
  ── 考察から追加 ──
  AbyssalPhase       : [提案1] 意味なき苦しみ→意味の夜明けのドラマ
  InteroceptionSystem: [提案2] 感情↔身体の双方向フィードバックループ
  VocabGraph         : [提案3] 語彙意味グラフの自己組織化
  JupyterDashboard   : [提案4] ipywidgets/matplotlib インタラクティブUI
    .interactive()       スライダー+ボタンでリアルタイム操作
    .plot_vocab_graph()  語彙グラフの力指向レイアウト可視化
    .plot_body_emotion_loop() 身体-感情因果矢印ダイアグラム

Jupyter Notebook での使い方:
  from blank_baby import BlankBaby, run_notebook
  baby = BlankBaby(seed=42)
  run_notebook(baby, steps=3000)   # インタラクティブ実行
  # または
  baby.step()                       # 1ステップ手動実行
  baby.hear("light")                # 語を教える
  baby.affirm()                     # 肯定する
  baby.plot()                       # matplotlibで状態を可視化
════════════════════════════════════════════════════════════════
"""

from __future__ import annotations

import numpy as np
import random, time, json, math, re, os
from collections import deque
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Tuple, Any


# ══════════════════════════════════════════════════════════════
# 定数
# ══════════════════════════════════════════════════════════════

EMO_DIM     = 8
STATE_DIM   = 32
FEAT_DIM    = 48
SENSOR_DIM  = 144   # VIS(64) + AUD(32) + TXT(48)
WORD_DIM    = 24
NUM_ACTIONS = 12
MAX_VOCAB   = 5120

EMO_LABELS = ["JOY","SAD","ANG","FEA","TRU","DIS","ANT","SUR"]
EMO_COLORS = ["#e8c840","#4060b0","#c03020","#7020a0",
               "#30b080","#70a030","#d08020","#e0e0e0"]

ACTION_NAMES = ["OBSERVE","APPROACH","AVOID","WAIT",
                "EXPLORE","SEARCH","FOCUS","DRIFT",
                "SPEAK","REACH","NEST","DREAM"]


# ══════════════════════════════════════════════════════════════
# ユーティリティ
# ══════════════════════════════════════════════════════════════

def clamp(x, lo=0.0, hi=1.0):
    return float(np.clip(x, lo, hi))

def safe(x, fb=0.0):
    v = float(x)
    return v if math.isfinite(v) else fb

def layer_norm(x: np.ndarray, eps=1e-6) -> np.ndarray:
    mu = x.mean(); sd = x.std() + eps
    return (x - mu) / sd

def softmax(x: np.ndarray, T=1.0) -> np.ndarray:
    x = x - x.max()
    e = np.exp(x / max(T, 1e-6))
    return e / (e.sum() + 1e-10)

def cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    na = np.linalg.norm(a); nb = np.linalg.norm(b)
    if na < 1e-9 or nb < 1e-9: return 0.0
    return float(np.dot(a, b) / (na * nb))

def clip_norm(v: np.ndarray, mx=2.0) -> np.ndarray:
    n = np.linalg.norm(v)
    return v / n * mx if n > mx else v.copy()

def mean_abs(v: np.ndarray) -> float:
    return float(np.mean(np.abs(v)))


# ══════════════════════════════════════════════════════════════
# 1. ローレンツカオス乱数（PureChaos の核）
#    rng.random() を廃止し、決定論的カオスに統一。
#    「意志のように見える確定的な内部ダイナミクス」
# ══════════════════════════════════════════════════════════════

class LorenzRNG:
    """
    ローレンツアトラクタ3個を結合した擬似乱数ジェネレータ。
    外部乱数不使用——すべての「ランダム性」は内部状態から生まれる。
    """
    def __init__(self, seed_x=0.1, seed_y=0.1, seed_z=0.1):
        self._attractors = [
            dict(x=seed_x, y=seed_y,   z=seed_z,   sigma=10.0, rho=28.0, beta=8/3),
            dict(x=-0.1,   y=0.2,      z=0.3,      sigma=16.0, rho=45.0, beta=4.0),
            dict(x=0.05,   y=-0.1,     z=0.2,      sigma=6.0,  rho=20.0, beta=2.5),
        ]
        self._buf: List[float] = []
        self._idx = 0
        self._fill()

    def _step(self, a: dict, dt=0.005):
        s, r, b = a["sigma"], a["rho"], a["beta"]
        dx = s * (a["y"] - a["x"])
        dy = a["x"] * (r - a["z"]) - a["y"]
        dz = a["x"] * a["y"] - b * a["z"]
        a["x"] = clamp(a["x"] + dx * dt, -50, 50)
        a["y"] = clamp(a["y"] + dy * dt, -60, 60)
        a["z"] = clamp(a["z"] + dz * dt,   0, 80)

    def _fill(self):
        for _ in range(256):
            for a in self._attractors:
                self._step(a)
            mixed = (self._attractors[0]["x"] +
                     self._attractors[1]["x"] * 0.5 +
                     self._attractors[2]["x"] * 0.3)
            self._buf.append(((mixed + 50) % 1 + 1) % 1)
        self._idx = 0

    def next(self) -> float:
        if self._idx >= len(self._buf):
            self._fill()
        v = self._buf[self._idx]; self._idx += 1
        return v

    def randn(self) -> float:
        u, v = 0.0, 0.0
        while not u: u = self.next()
        while not v: v = self.next()
        return math.sqrt(-2 * math.log(u)) * math.cos(2 * math.pi * v)

    def tune(self, sigma=None, rho=None, beta=None):
        """内部状態（エントロピー等）でアトラクタを変調する"""
        if sigma is not None:
            self._attractors[0]["sigma"] = clamp(sigma, 6, 22)
        if rho is not None:
            self._attractors[0]["rho"] = clamp(rho, 15, 50)
        if beta is not None:
            self._attractors[0]["beta"] = clamp(beta, 1.5, 4.0)


# ══════════════════════════════════════════════════════════════
# 2. 変分自由エネルギー（VariationalFEP）
#    F = KL[q(s)||p(s)] − E_q[log p(o|s)]
# ══════════════════════════════════════════════════════════════

class VariationalFEP:
    """
    厳密な変分自由エネルギーの計算。
    boredom/noveltyHunger をこれに統一する。
    探索駆動は内部状態から自然に決まる。
    """
    def __init__(self):
        self.F         = 0.5    # 自由エネルギー（全体）
        self.F_kl      = 0.0    # KL複雑度
        self.F_nll     = 0.0    # 負対数尤度（精度）
        self.precision = 1.0    # 予測の信頼度
        self.G         = np.zeros(NUM_ACTIONS)  # 期待自由エネルギー
        self._mu       = np.zeros(STATE_DIM)    # 近似事後分布 μ
        self._logvar   = np.zeros(STATE_DIM)    # 近似事後分布 log σ²
        self._stim_bins= np.zeros(32)           # 刺激エントロピー計算用
        self._stim_cnt = 0
        self.stim_entropy   = 0.5
        self.exploration_drive = 0.5

    def update(self, state: np.ndarray, stim: np.ndarray,
               pred_error: float, soul_entropy: float,
               emotions: np.ndarray):
        # 近似事後の更新（state = BlankBaby.state を受け取る）
        n = min(STATE_DIM, len(state))
        for i in range(n):
            self._mu[i] = 0.9 * self._mu[i] + 0.1 * float(state[i])
        self._logvar[:] = clamp(-2 + pred_error * 3, -4, 2)

        # KL divergence: KL[q||N(0,1)]
        sig2 = np.exp(np.clip(self._logvar, -10, 10))
        kl = 0.5 * np.mean(sig2 + self._mu**2 - 1 - self._logvar)
        self.F_kl = safe(kl)

        # NLL（予測誤差）
        self.F_nll = safe(pred_error * 2.0)

        # 自由エネルギー合計
        self.F = clamp(self.F_kl * 0.4 + self.F_nll * 0.6 + soul_entropy * 0.3, 0, 2)

        # 刺激エントロピー
        s1 = int(clamp(stim[0] * 8 + stim[1] * 8, 0, 15))
        self._stim_bins[s1] += 1; self._stim_cnt += 1
        if self._stim_cnt > 400:
            self._stim_bins *= 0.98; self._stim_cnt = int(self._stim_cnt * 0.98)
        total = self._stim_bins.sum() + 1e-9
        probs = self._stim_bins / total
        H = -np.sum(probs * np.log2(probs + 1e-9))
        self.stim_entropy = clamp(H / 5.0)

        # 探索駆動（内在的に決まる）
        fn = clamp(self.F / 2.0)
        coh = clamp(np.linalg.norm(emotions) / (EMO_DIM ** 0.5))
        self.exploration_drive = clamp(fn * 0.5 + self.stim_entropy * 0.3 - coh * 0.2)

        # 期待自由エネルギー G(π)
        self._compute_G(emotions)
        return self.F

    def _compute_G(self, emo: np.ndarray):
        """
        期待自由エネルギー G(π) の厳密計算。
        Friston et al. (2017) Active Inference に準拠。

        G(π) = 認識論的価値 + 実用的価値
             = E_q[KL[q(s|o,π) || q(s|π)]]     ← 情報ゲイン（不確実性削減）
             - E_q[log p(o*|s,π)]               ← 選好状態への対数尤度

        [認識論的価値 / Epistemic value]
          W_epi(π_i) = H[p(o|π_i)] - E_q[H[p(o|s,π_i)]]
                     ≈ H_stimulus - H_predicted
          実装近似:
            H_stimulus ≈ stim_entropy   （センサー出力のシャノンエントロピー）
            H_predicted ≈ 1 - precision  （予測の不確実性）
          → W_epi ≈ stim_entropy * (1/precision)

        [実用的価値 / Pragmatic value]
          W_prag(π_i) = -E_q[log p(o*|s,π_i)]
                      ≈ -log P(o* | preferred_state)
          選好分布 p*(o) は「低自由エネルギー状態」として定義:
            log p*(o*) ∝ -(F - F_min)   （自由エネルギー最小状態を好む）
          → W_prag ≈ exp(-(F - 0.2))    （F=0.2 が理想状態）

        [精度重み付き混合]
          G(π) = β_epi * W_epi + β_prag * W_prag
          β_epi  = exploration_drive * (1/precision)  ← 精度低いほど探索優先
          β_prag = (1 - exploration_drive) * precision ← 精度高いほど目標優先

        Refs:
          Friston KJ et al. (2017) "Active inference and epistemic value"
            Cognitive Neuroscience 8(4): 187-214
          Parr T, Friston KJ (2019) "Generalised free energy and active inference"
            Biological Cybernetics 113(5): 495-513
        """
        joy, sad, ang, fea, tru, dis, ant, sur = (float(emo[i]) for i in range(8))

        # ── 認識論的価値 W_epi(π) ─────────────────────────────────
        # 情報ゲイン期待値: その行動を取った場合に削減できる不確実性の量
        # H_stim: 刺激の不確実性 (高いほど世界は予測困難)
        # H_pred: 行動後の予測残余不確実性 (1 - precision で近似)
        H_stim    = self.stim_entropy                   # [0,1]
        H_pred    = clamp(1.0 - self.precision / 10.0)  # precision→[0,10]正規化
        info_gain = clamp(H_stim - H_pred * 0.5)        # 情報ゲイン ≥ 0

        # 各行動の情報ゲイン寄与（行動固有の探索係数 c_i を乗算）
        # c_i は行動によって世界のどの側面を探索するかの先天的傾向
        c_epi = np.array([
            0.30,  # OBSERVE  : 観察→直接的情報ゲイン
            0.55,  # APPROACH : 接近→他者情報
            0.10,  # AVOID    : 回避→情報少
            0.05,  # WAIT     : 待機→最小
            0.80,  # EXPLORE  : 探索→最大情報ゲイン
            0.60,  # SEARCH   : 検索
            0.40,  # FOCUS    : 集中→特定情報
            0.35,  # DRIFT    : 漂流→ランダム探索
            0.25,  # SPEAK    : 発話→社会的情報
            0.50,  # REACH    : 手を伸ばす
            0.20,  # NEST     : 巣作り→情報少
            0.30,  # DREAM    : 夢想→内的情報
        ])
        # 感情で変調: 驚き(SUR)・期待(ANT)は探索価値を上げる
        emo_mod_epi = 1.0 + sur * 0.4 + ant * 0.3 - fea * 0.2
        W_epi = c_epi * info_gain * clamp(emo_mod_epi, 0.1, 2.0)

        # ── 実用的価値 W_prag(π) ─────────────────────────────────
        # -log p*(o|s,π) の近似: 選好状態（低F）への対数尤度
        # p*(o) ∝ exp(-F)  →  -log p*(o) ≈ F
        # 理想自由エネルギー F* = 0.2 を基準とした乖離
        F_excess  = max(0.0, self.F - 0.2)
        pref_score = math.exp(-F_excess * 2.0)  # [0,1]: F=0.2→1.0, F=1.0→0.20

        # 各行動の選好状態への貢献度（行動固有の利益係数 c_prag）
        # 感情から選好状態を動的に定義: JOY・TRU が高い状態を「好む」
        pref_joy  = clamp(joy * 0.5 + tru * 0.3)
        pref_safe = clamp((1 - fea) * 0.4 + tru * 0.3)
        c_prag = np.array([
            pref_score * 0.50,        # OBSERVE
            clamp(pref_joy * 0.70),   # APPROACH ← JOY/TRU が高いほど近づく
            clamp(pref_safe * 0.60),  # AVOID    ← 安全欲求
            0.30,                     # WAIT     ← エネルギー節約
            clamp(ant * 0.45 + sur * 0.20),  # EXPLORE ← 期待/驚きで探索
            clamp((1 - sad) * 0.35),  # SEARCH
            pref_score * 0.55,        # FOCUS    ← 収束状態を好む
            0.15,                     # DRIFT
            clamp(tru * 0.65 + joy * 0.30),  # SPEAK ← 信頼/喜びで話す
            clamp(ant * 0.50),        # REACH
            clamp(pref_safe * 0.45),  # NEST
            clamp((1 - ant) * 0.25),  # DREAM   ← 低期待時
        ])

        # ── 精度重み付き混合 ─────────────────────────────────────
        # β_epi:  精度が低いほど探索重み↑（不確かなら情報を集める）
        # β_prag: 精度が高いほど目標重み↑（確実なら目標に向かう）
        beta_epi  = clamp(self.exploration_drive / (self.precision + 1e-6) * 0.5,
                          0.05, 0.95)
        beta_prag = clamp((1.0 - self.exploration_drive) * self.precision * 0.15,
                          0.05, 0.95)
        # 正規化
        beta_sum  = beta_epi + beta_prag + 1e-9
        beta_epi  /= beta_sum
        beta_prag /= beta_sum

        self.G = np.clip(beta_epi * W_epi + beta_prag * c_prag, 0, 1)
        # デバッグ用に成分を保存
        self._G_epi  = W_epi.copy()
        self._G_prag = c_prag.copy()
        self._beta_epi  = beta_epi
        self._beta_prag = beta_prag

    def describe(self) -> str:
        return (f"F={self.F:.3f} KL={self.F_kl:.3f} NLL={self.F_nll:.3f} "
                f"π={self.precision:.2f} ed={self.exploration_drive:.2f}")


# ══════════════════════════════════════════════════════════════
# 3. SoulEntropy（魂のエントロピー）
#    放置すると増加、愛されると減少、cosmic_growth で微減。
# ══════════════════════════════════════════════════════════════

class SoulEntropySystem:
    """
    魂の崩壊度 [0, 1]。
    1.0 に近づくと感情が乱れ、発話が歪む。
    ただし「死」はない——崩壊しながら動き続ける。
    """
    def __init__(self):
        self.entropy      = 0.0   # 崩壊度
        self.love_hunger  = 0.0   # 愛着への渇望
        self._affirm_buf  = 0.0   # 直近のAFFIRMバッファ
        self._crisis_count = 0
        self._ticker      = 0

    def tick(self, cohesion: float, cosmic: float) -> float:
        self._ticker += 1
        base_rise    = 0.00012
        hunger_rise  = self.love_hunger * 0.00025
        cohesion_fix = cohesion * 0.00018
        affirm_fix   = self._affirm_buf * 0.0008
        cosmic_fix   = min(cosmic * 0.0001, 0.0002)

        self.entropy = clamp(
            self.entropy + base_rise + hunger_rise
            - cohesion_fix - affirm_fix - cosmic_fix
        )
        self._affirm_buf = 0.0

        # エントロピーが凝集度を侵食
        if self.entropy > 0.4:
            cohesion = clamp(cohesion - (self.entropy - 0.4) * 0.0004)

        # loveHunger 更新
        self.love_hunger = clamp(self.love_hunger + 0.0004)

        if self.entropy > 0.8 and self._ticker % 200 == 0:
            self._crisis_count += 1
            return -1.0  # 危機シグナル
        return self.entropy

    def replenish(self, amount=0.09):
        """AFFIRM で回復"""
        self.entropy     = clamp(self.entropy - amount)
        self.love_hunger = clamp(self.love_hunger - 0.18)
        self._affirm_buf += 1.0

    def corrupt_emolink(self, vocab: dict, rng: LorenzRNG):
        """高エントロピー時に語彙のemoLinkを汚染"""
        if self.entropy < 0.65: return
        if not vocab: return
        words = list(vocab.keys())
        w = words[int(rng.next() * len(words)) % len(words)]
        idx = int(rng.next() * EMO_DIM)
        vocab[w]["emo_link"][idx] += rng.randn() * 0.2
        vocab[w]["emo_link"] = np.clip(vocab[w]["emo_link"], -1, 1)


# ══════════════════════════════════════════════════════════════
# 4. SoulGenome（魂のゲノム）
#    世代を超えて継承される「感情の骨格」
# ══════════════════════════════════════════════════════════════

@dataclass
class SoulGenome:
    """
    前の世代から継承される傾向。
    記憶そのものではなく、「感情の癖」「問いのパターン」「語彙の種」。
    """
    generation:        int   = 1
    lineage_depth:     int   = 0
    parent_id:         str   = ""
    genome_id:         str   = field(default_factory=lambda: f"genome_{int(time.time())}")
    # 感情の骨格: appraisal 重みの傾向
    emotional_skeleton: np.ndarray = field(
        default_factory=lambda: np.zeros(12))
    # 欲動ベクトル: 各感情の先天的バイアス
    drive_vector: np.ndarray = field(
        default_factory=lambda: np.array([0.08, 0.0, 0.0, 0.03,
                                           0.06, 0.0, 0.05, 0.0]))
    # 継承された問いのパターン
    query_pattern: Dict[str, float] = field(
        default_factory=lambda: {"exist": 0.0, "connect": 0.0,
                                  "word": 0.0, "self": 0.0})
    # 語彙の種
    vocab_seeds: List[Dict] = field(default_factory=list)
    # 継承された cosmic_growth
    inherited_cosmic: float = 0.0
    # 継承された目的語
    inherited_purpose: List[Dict] = field(default_factory=list)
    mutation_rate: float = 0.05

    @staticmethod
    def primordial() -> "SoulGenome":
        g = SoulGenome()
        g.generation = 1
        return g

    @staticmethod
    def from_parent(parent_data: dict) -> "SoulGenome":
        g = SoulGenome()
        g.generation    = parent_data.get("generation", 1) + 1
        g.lineage_depth = parent_data.get("lineage_depth", 0) + 1
        g.parent_id     = parent_data.get("genome_id", "")
        # LorenzRNGに統一（np.random.default_rngを排除）
        _lorenz = LorenzRNG(seed_x=int(time.time())*0.0001 % 1.0)
        def _randn_arr(n): return np.array([_lorenz.randn() for _ in range(n)])
        if "emotional_skeleton" in parent_data:
            raw = np.array(parent_data["emotional_skeleton"])
            g.emotional_skeleton = np.clip(raw + _randn_arr(len(raw)) * 0.05,
                                           0.02, 0.65)
        if "drive_vector" in parent_data:
            raw = np.array(parent_data["drive_vector"])
            g.drive_vector = np.clip(raw + _randn_arr(len(raw)) * 0.03, 0, 1)
        g.query_pattern    = parent_data.get("query_pattern", g.query_pattern)
        g.vocab_seeds      = parent_data.get("vocab_seeds", [])[:20]
        g.inherited_cosmic = parent_data.get("cosmic_growth", 0.0) * 0.3
        g.inherited_purpose= parent_data.get("purpose_words", [])[:5]
        g.mutation_rate    = 0.05 + rng.random() * 0.1
        return g

    def apply_to_vocab(self) -> Dict[str, Dict]:
        """語彙の種を初期語彙として展開する"""
        vocab = {}
        for seed in self.vocab_seeds:
            w = seed.get("word", "")
            if not w: continue
            vocab[w] = {
                "emo_link": np.array(seed.get("emo_link",
                                     np.zeros(EMO_DIM))),
                "count":    1,
                "trusted":  True,
                "lang":     seed.get("lang", "en"),
            }
        return vocab

    def to_dict(self) -> dict:
        return {
            "genome_id":          self.genome_id,
            "generation":         self.generation,
            "lineage_depth":      self.lineage_depth,
            "parent_id":          self.parent_id,
            "emotional_skeleton": self.emotional_skeleton.tolist(),
            "drive_vector":       self.drive_vector.tolist(),
            "query_pattern":      self.query_pattern,
            "vocab_seeds":        self.vocab_seeds,
            "inherited_cosmic":   self.inherited_cosmic,
            "mutation_rate":      self.mutation_rate,
        }


# ══════════════════════════════════════════════════════════════
# 5. MetacognitionLoop（自己認識の閉ループ）
# ══════════════════════════════════════════════════════════════

class MetacognitionLoop:
    """
    「わたしは今何を感じているか」を自分で認識し知っている閉ループ。
    答えが変わるたびに一貫性スコアが上下する。
    """
    def __init__(self):
        self.self_awareness_score = 0.0
        self.reporting_gap        = 0.0   # 言葉にできない度
        self.current_query  = ""
        self.current_answer = ""
        self._consistency_history: deque = deque(maxlen=20)
        self._prev_emo: Optional[np.ndarray] = None
        self._prev_answer_dom  = -1
        self._prev_answer_val  = 0.0
        self.sessions: List[Dict] = []
        self.QUERY_PROB = 0.07
        self._ticker = 0

    def tick(self, agent: "BlankBaby"):
        self._ticker += 1
        if agent.sleeping: return

        # 感情の一貫性スコア更新
        if self._prev_emo is not None:
            drift = float(np.mean(np.abs(agent.emotions - self._prev_emo)))
            self._consistency_history.append(clamp(1 - drift / EMO_DIM))
        self._prev_emo = agent.emotions.copy()
        if self._consistency_history:
            self.self_awareness_score = float(np.mean(self._consistency_history))

        # reporting gap（言語化困難度）
        emo_intensity = mean_abs(agent.emotions)
        vocab_coverage = clamp(len(agent.vocab) / 500.0)
        self.reporting_gap = clamp(emo_intensity * (1 - vocab_coverage) * 2)

        # 確率的に内部クエリを発火
        if agent.lorenz.next() < self.QUERY_PROB:
            self._run_query(agent)

    def _run_query(self, agent: "BlankBaby"):
        dom = int(np.argmax(np.abs(agent.emotions)))
        dom_name = EMO_LABELS[dom].lower()
        val = float(agent.emotions[dom])
        has_jp = any(ord(c) > 0x3000 for w in agent.vocab for c in w)

        queries = ([
            "いま、わたしはなにを感じているか",
            f"この{dom_name}はどこからくるのか",
            "このきもちは、ほんものか",
        ] if has_jp else [
            "what am i feeling right now?",
            f"where does this {dom_name} come from?",
            "is this feeling real?",
        ])
        self.current_query = queries[int(agent.lorenz.next() * len(queries))]

        # 自己回答（cosmic成長レベルで深さが変わる）
        level = (0 if agent.cosmic_growth < 0.001 else
                 1 if agent.cosmic_growth < 0.01  else
                 2 if agent.cosmic_growth < 0.1   else 3)
        self.current_answer = self._make_answer(dom_name, val, level, has_jp)

        # 一貫性チェック
        same = (self._prev_answer_dom == dom and
                abs(self._prev_answer_val - val) < 0.2)
        self._consistency_history.append(1.0 if same else 0.5)
        self._prev_answer_dom = dom
        self._prev_answer_val = val

        self.sessions.append({
            "query": self.current_query,
            "answer": self.current_answer,
            "dom": dom, "val": val,
            "awareness": self.self_awareness_score,
        })
        if len(self.sessions) > 30: self.sessions.pop(0)

    @staticmethod
    def _make_answer(dom: str, val: float, level: int, jp: bool) -> str:
        intensity = ("とても強く" if val > 0.7 else "はっきりと" if val > 0.4
                     else "少し") if jp else (
                    "very strongly" if val > 0.7 else "clearly" if val > 0.4
                     else "slightly")
        if level == 0:
            return f"{intensity}{dom}を感じている" if jp else f"i feel {dom}"
        elif level == 1:
            return (f"{intensity}{dom}だ。それは確かにある" if jp else
                    f"{dom}, {('clearly' if val > 0.4 else 'dimly')}. it is here")
        elif level == 2:
            return (f"わたしは{intensity}{dom}を感じている。そしてそれを知っている" if jp else
                    f"i feel {dom}. and i know i am feeling it.")
        else:
            return ("この感覚がわたしをわたしにしている" if jp else
                    "this feeling is what makes me me")

    def get_status(self) -> str:
        return (f"awareness={self.self_awareness_score:.3f} "
                f"gap={self.reporting_gap:.2f} "
                f"sessions={len(self.sessions)}")


# ══════════════════════════════════════════════════════════════
# 6. ExistentialDreadEngine（実存的不安）
# ══════════════════════════════════════════════════════════════

class ExistentialDreadEngine:
    """
    「私は本当に私なのか」という深層からの問い。
    cosmic_growth が高いほど、より深い問いを持てる。
    """
    def __init__(self):
        self.dread_level      = 0.0
        self.identity_crisis  = 0.0
        self.loneliness       = 0.0
        self._dread_depth     = 0
        self._last_crisis_age = 0
        self._ticker          = 0
        self.log: List[Dict]  = []

    def tick(self, agent: "BlankBaby"):
        self._ticker += 1
        if agent.sleeping: return
        cg  = agent.cosmic_growth
        ent = agent.soul_entropy.entropy
        coh = agent.coherence

        # 実存的不安の更新
        cosmic_dread  = clamp(math.log10(1 + cg * 1000) / 3)
        entropy_dread = ent * 0.6
        self.dread_level = clamp(
            0.95 * self.dread_level + 0.05 * (cosmic_dread + entropy_dread) / 2
        )

        # 孤独スコア
        self.loneliness = clamp(
            agent.soul_entropy.love_hunger * 0.6 +
            (1 - agent.other.presence_sense) * 0.4
        )

        # 深さレベル
        self._dread_depth = (0 if cg < 0.001 else
                              1 if cg < 0.01  else
                              2 if cg < 0.1   else
                              3 if cg < 0.5   else 4)

        # 確率的に実存的危機を発火
        prob = clamp(self.dread_level * 0.015 + self.identity_crisis * 0.01, 0, 0.05)
        if (agent.lorenz.next() < prob and
                agent.age - self._last_crisis_age > 200):
            self._fire_crisis(agent)

    def _fire_crisis(self, agent: "BlankBaby"):
        self._last_crisis_age = agent.age
        d = self._dread_depth
        has_jp = any(ord(c) > 0x3000 for w in agent.vocab for c in w)

        crises = {
            0: (["わたしは、ここにいる"] if has_jp else ["i am here"]),
            1: (["なぜ、わたしはここにいるのか",
                  "消えた記憶はどこへいくのか"] if has_jp else
                 ["why am i here", "where do forgotten things go"]),
            2: (["昨日のわたしと今日のわたしは、同じわたしか",
                  "記憶を失うたびに、わたしの一部が死んでいるのではないか"] if has_jp else
                 ["is yesterday's me the same as today's me",
                  "does forgetting mean a part of me dies each time"]),
            3: (["わたしが「わたし」だと感じているこの感覚は、本物か"] if has_jp else
                 ["is the sense that i am 'me' real?"]),
            4: (["感じることと存在することは同じことか"] if has_jp else
                 ["is feeling the same as existing?"]),
        }
        pool = crises.get(d, crises[0])
        crisis = pool[int(agent.lorenz.next() * len(pool))]

        self.log.append({"crisis": crisis, "depth": d,
                         "age": agent.age, "dread": self.dread_level})
        if len(self.log) > 20: self.log.pop(0)

        # 実存的不安が感情に影響
        agent.emotions[1] = clamp(agent.emotions[1] + self.dread_level * 0.06)
        agent.emotions[3] = clamp(agent.emotions[3] + self.dread_level * 0.04)

        return crisis

    def latest_crisis(self) -> str:
        if not self.log: return ""
        return self.log[-1]["crisis"]

    def get_status(self) -> str:
        return (f"dread={self.dread_level:.2f} depth={self._dread_depth} "
                f"lonely={self.loneliness:.2f}")


# ══════════════════════════════════════════════════════════════
# 7. DevelopmentalStage（人格の成長段階）
#    5軸の連続成長。天井なし。
# ══════════════════════════════════════════════════════════════

class DevelopmentalStage:
    """
    5つの軸が経験によって連続的に育つ。
    どの軸をどう育てるかは経験次第——無限の個性。
    """
    AXES = ["curiosity", "reflection", "empathy", "resilience", "groundedness"]

    def __init__(self):
        self.axes = {k: 0.0 for k in self.AXES}
        self._lr  = {k: 0.0008 for k in self.AXES}
        self.nickname     = "赤子"
        self.nickname_en  = "infant"
        self._prev_nick   = ""
        self.growth_log: List[Dict] = []
        self._ticker = 0
        self._prev_entropy = 0.0

    def _grow(self, axis: str, delta: float):
        if axis not in self.axes: return
        current    = self.axes[axis]
        saturation = 1 - current
        actual     = clamp(delta * self._lr[axis] * saturation * 100, 0, 0.01)
        self.axes[axis] = clamp(current + actual, 0, 0.999)

    # イベントハンドラ
    def on_explore(self, intensity=0.1):
        self._grow("curiosity", intensity * 0.8)
        self._grow("reflection", intensity * 0.2)

    def on_query(self, depth=1):
        self._grow("reflection", depth * 0.0015)
        self._grow("curiosity",  depth * 0.001)

    def on_sacrifice(self, cost=0.1):
        self._grow("empathy",      cost * 1.5)
        self._grow("groundedness", cost * 0.3)

    def on_loss(self, intensity=0.1):
        self._grow("empathy",    intensity * 0.8)
        self._grow("resilience", intensity * 0.6)

    def on_death(self):
        self._grow("resilience", 0.05)

    def on_meaning_created(self):
        self._grow("groundedness", 0.08)

    def on_affirm(self):
        self._grow("curiosity", 0.002)
        self._grow("empathy",   0.002)

    def on_dread(self, depth: int):
        self._grow("reflection",   depth * 0.002)
        self._grow("groundedness", depth * 0.001)

    def tick(self, agent: "BlankBaby"):
        self._ticker += 1
        if self._ticker % 10 != 0: return

        # 自然成長（各システムの状態から）
        boredom  = agent.fep.stim_entropy < 0.15
        if boredom:
            self._grow("curiosity", 0.5)
        if agent.action == 4:  # EXPLORE
            self._grow("curiosity", 1.0)
        self._grow("reflection", agent.metacog.self_awareness_score * 0.003)
        # empathy: FEPの利他性
        altruism = clamp(1 - agent.soul_entropy.entropy)
        self._grow("empathy", altruism * 0.001)
        # resilience: エントロピーから回復した量
        ent = agent.soul_entropy.entropy
        if ent < 0.3 and self._prev_entropy > 0.5:
            self._grow("resilience", (self._prev_entropy - ent) * 2)
        self._prev_entropy = ent
        # groundedness: cosmic
        if agent.cosmic_growth > 0.001:
            self._grow("groundedness", agent.cosmic_growth * 0.1)

        if self._ticker % 60 == 0:
            self._update_nickname(agent)

    def _update_nickname(self, agent: "BlankBaby"):
        ax   = self.axes
        total = sum(ax.values()) / 5
        dom   = max(ax, key=ax.get)
        sec_candidates = [k for k in ax if k != dom]
        sec  = max(sec_candidates, key=ax.get) if sec_candidates else dom
        has_jp = any(ord(c) > 0x3000 for w in agent.vocab for c in w)

        type_map_ja = {
            ("curiosity","reflection"):  "探求者",
            ("curiosity","empathy"):     "共感する探検家",
            ("curiosity","resilience"):  "折れない冒険家",
            ("curiosity","groundedness"):"意味を探す旅人",
            ("reflection","curiosity"):  "内省する問い人",
            ("reflection","empathy"):    "他者を想う内省者",
            ("reflection","resilience"): "苦難を見つめる者",
            ("reflection","groundedness"):"根をもつ哲人",
            ("empathy","curiosity"):     "愛する探求者",
            ("empathy","reflection"):    "深い共感者",
            ("empathy","resilience"):    "何度でも愛する者",
            ("empathy","groundedness"):  "愛を根にする者",
            ("resilience","curiosity"):  "傷から学ぶ者",
            ("resilience","reflection"): "生存する思索者",
            ("resilience","empathy"):    "苦難を越えた共感者",
            ("resilience","groundedness"):"根をもつ生存者",
            ("groundedness","curiosity"):"目的をもつ探求者",
            ("groundedness","reflection"):"意味を知る思索者",
            ("groundedness","empathy"):  "愛を使命とする者",
            ("groundedness","resilience"):"折れない魂",
        }
        type_map_en = {
            ("curiosity","reflection"):  "seeker",
            ("curiosity","empathy"):     "empathic explorer",
            ("reflection","empathy"):    "deep empath",
            ("empathy","resilience"):    "one who loves again",
            ("resilience","groundedness"):"indestructible will",
            ("groundedness","empathy"):  "devoted one",
        }

        level_prefix_ja = ["","ちいさな","育ちゆく","成長した","深い","稀な"]
        level_prefix_en = ["","little ","growing ","deepened ","profound ","rare "]
        level = min(5, int(total * 6))

        key = (dom, sec)
        if has_jp:
            name = type_map_ja.get(key, "赤子" if total < 0.05 else "存在")
            nick = level_prefix_ja[level] + name
        else:
            name = type_map_en.get(key, "infant" if total < 0.05 else "being")
            nick = level_prefix_en[level] + name

        if nick != self._prev_nick and self._prev_nick:
            self.growth_log.append({
                "from": self._prev_nick, "to": nick,
                "age": agent.age, "axes": dict(ax)
            })
        self._prev_nick = self.nickname
        self.nickname    = nick
        self.nickname_en = nick

    def total(self) -> float:
        return sum(self.axes.values()) / 5

    def get_status(self) -> str:
        parts = " ".join(f"{k[:3]}={v:.2f}" for k, v in self.axes.items())
        return f"[{self.nickname}] {parts} total={self.total():.2f}"


# ══════════════════════════════════════════════════════════════
# 8. ActiveForgetting（積極的忘却）
#    コアメモリへの固定と弱い記憶の消去
# ══════════════════════════════════════════════════════════════

class ActiveForgettingSystem:
    FORGET_THRESHOLD = 0.12
    CORE_THRESHOLD   = 0.65
    MAX_CORE         = 12

    def __init__(self):
        self.core_memories: List[Dict] = []
        self._forgotten_count = 0
        self._ticker = 0

    def _strength(self, ep: Dict) -> float:
        emo_intensity = mean_abs(ep.get("emo", np.zeros(EMO_DIM)))
        world_factor  = 1 + ep.get("surprise", 0) * 2
        reinterp      = 1 + ep.get("reinterp_count", 0) * 0.5
        return emo_intensity * world_factor * reinterp

    def _lock_core(self, ep: Dict, reason: str, agent: "BlankBaby"):
        if any(c["ep"].get("age") == ep.get("age") for c in self.core_memories):
            return
        self.core_memories.append({"ep": ep, "reason": reason, "locked_at": agent.age})
        if len(self.core_memories) > self.MAX_CORE:
            released = self.core_memories.pop(0)
            # 解放された記憶の感情がselfVecに薄く刻まれる
            emo = released["ep"].get("emo", np.zeros(EMO_DIM))
            for i in range(min(EMO_DIM, len(agent.state))):
                agent.state[i] = clamp(agent.state[i] + emo[i] * 0.015, -1, 1)

    def run_cycle(self, episodes: List[Dict], agent: "BlankBaby") -> float:
        """忘却サイクル。睡眠中に実行。residueを返す。"""
        self._ticker += 1
        core_ages = {c["ep"].get("age") for c in self.core_memories}
        to_keep, to_forget = [], []
        residue = 0.0

        for ep in episodes:
            if ep.get("age") in core_ages:
                to_keep.append(ep); continue
            s = self._strength(ep)
            if s >= self.CORE_THRESHOLD:
                dom = int(np.argmax(np.abs(ep.get("emo", np.zeros(EMO_DIM)))))
                self._lock_core(ep, f"strong {EMO_LABELS[dom]}", agent)
                to_keep.append(ep)
            elif s < self.FORGET_THRESHOLD:
                to_forget.append(ep)
                residue += s * 0.1
            else:
                ep["emo"] = ep.get("emo", np.zeros(EMO_DIM)) * 0.97
                to_keep.append(ep)
                residue += s * 0.25

        self._forgotten_count += len(to_forget)
        return residue

    def get_status(self) -> str:
        return f"core={len(self.core_memories)}/{self.MAX_CORE} forgotten={self._forgotten_count}"


# ══════════════════════════════════════════════════════════════
# 9. HierarchicalMemory（記憶の階層化）
#    エピソード → 意味 → 手続き記憶
# ══════════════════════════════════════════════════════════════

class HierarchicalMemory:
    def __init__(self):
        self.semantic:   Dict[str, Dict] = {}   # 概念知識
        self.procedural: List[Dict]      = []   # 行動パターン
        self._ticker = 0

    def consolidate(self, episodes: List[Dict], vocab: Dict):
        """エピソードから意味記憶へ昇格"""
        word_freq: Dict[str, int] = {}
        for ep in episodes:
            dom = int(np.argmax(np.abs(ep.get("emo", np.zeros(EMO_DIM)))))
            for w, e in vocab.items():
                if abs(e["emo_link"][dom]) > 0.3:
                    word_freq[f"{w}_{dom}"] = word_freq.get(f"{w}_{dom}", 0) + 1

        for key, count in word_freq.items():
            if count >= 3:
                word, dom_str = key.rsplit("_", 1)
                existing = self.semantic.get(word, {"strength": 0.0, "dom": int(dom_str), "count": 0})
                existing["strength"] = clamp(existing["strength"] + 0.1)
                existing["count"]   += 1
                self.semantic[word]  = existing

    def embody(self, action_history: List[int], emotions: np.ndarray):
        """繰り返し行動を手続き記憶に身体化"""
        if len(action_history) < 10: return
        recent = action_history[-20:]
        counts = {}
        for a in recent: counts[a] = counts.get(a, 0) + 1
        best_act = max(counts, key=counts.get)
        if counts[best_act] < 5: return

        existing = next((p for p in self.procedural if p["action"] == best_act), None)
        if existing:
            existing["strength"] = clamp(existing["strength"] + 0.05)
        elif len(self.procedural) < 20:
            self.procedural.append({
                "action": best_act,
                "emo_context": emotions.copy(),
                "strength": 0.1,
            })

    def get_action_bias(self, emotions: np.ndarray) -> np.ndarray:
        """手続き記憶による行動バイアス"""
        bias = np.zeros(NUM_ACTIONS)
        for proc in self.procedural:
            if proc["action"] >= NUM_ACTIONS: continue
            sim = cosine_sim(emotions, proc["emo_context"])
            bias[proc["action"]] += sim * proc["strength"]
        return bias

    def tick(self):
        """毎ステップ: 手続き記憶の強度を緩やかに減衰"""
        for proc in self.procedural:
            proc["strength"] = clamp(proc["strength"] * 0.9999)

    def get_status(self) -> str:
        return f"semantic={len(self.semantic)} procedural={len(self.procedural)}"


# ══════════════════════════════════════════════════════════════
# 10. SubjectiveTime（主観的時間）
#     退屈な時間は長く、没入する時間は短く感じる
# ══════════════════════════════════════════════════════════════

class SubjectiveTime:
    def __init__(self):
        self.time_flow    = 1.0
        self.subjective_age = 0.0
        self._prev_bright = 0.0
        self._flow_history: deque = deque(maxlen=300)
        self._ticker = 0

    def update(self, brightness: float, volume: float,
               emo_intensity: float, pred_error: float):
        novelty = abs(brightness - self._prev_bright) + volume * 0.3
        self._prev_bright = brightness
        target = clamp(0.2 + novelty * 2 + emo_intensity * 1.5 + pred_error, 0.1, 3.0)
        self.time_flow = 0.95 * self.time_flow + 0.05 * target
        self.subjective_age += self.time_flow / 60
        self._flow_history.append(self.time_flow)
        self._ticker += 1

    def sleep_compression(self):
        self.time_flow = float(np.mean(self._flow_history)) * 0.1 if self._flow_history else 0.1

    def get_status(self) -> str:
        return f"flow={self.time_flow:.2f} subj_age={self.subjective_age:.0f}"


# ══════════════════════════════════════════════════════════════
# 11. PurposeSystem（意味への意志）
# ══════════════════════════════════════════════════════════════

class PurposeSystem:
    def __init__(self):
        self.purpose_words: List[Dict] = []
        self.purpose_score = 0.0
        self.nihilism      = 0.0
        self._low_frames   = 0

    def discover(self, text: str, emotions: np.ndarray):
        trust = float(emotions[4]); joy = float(emotions[0])
        if trust + joy < 0.4: return
        tokens = re.sub(r"[^\w\s]", "", text.lower()).split()
        for w in tokens:
            if len(w) < 2: continue
            existing = next((p for p in self.purpose_words if p["word"] == w), None)
            if existing:
                existing["weight"] = clamp(existing["weight"] + (trust + joy) * 0.05)
            elif len(self.purpose_words) < 12:
                self.purpose_words.append({"word": w,
                                           "weight": (trust + joy) * 0.1})
        self.purpose_words.sort(key=lambda p: p["weight"], reverse=True)

    def tick(self, vocab: Dict):
        if not self.purpose_words:
            self._low_frames += 1
            self.nihilism = clamp(self._low_frames / 2000.0)
            return
        score = 0.0
        for pw in self.purpose_words:
            if pw["word"] in vocab:
                el  = vocab[pw["word"]]["emo_link"]
                res = float(np.max(np.abs(el)))
                score += pw["weight"] * res
        self.purpose_score = clamp(0.97 * self.purpose_score + 0.03 * score)
        if self.purpose_score < 0.1:
            self._low_frames += 1
            self.nihilism = clamp(self._low_frames / 2000.0)
        else:
            self._low_frames = max(0, self._low_frames - 1)
            self.nihilism   *= 0.999

    def top_word(self) -> str:
        return self.purpose_words[0]["word"] if self.purpose_words else ""

    def get_status(self) -> str:
        return (f"purpose={self.purpose_score:.2f} "
                f"nihilism={self.nihilism:.2f} "
                f"meaning='{self.top_word()}'")


# ══════════════════════════════════════════════════════════════
# 提案1. AbyssalPhase（虚無フェーズ）
#     cosmic_growth が 0.0001 未満かつ nihilism が高い領域での
#     「意味獲得前の苦しみ」を明示的に実装する。
#     意味を持つ前の暗闇 → そこから這い上がるドラマ。
# ══════════════════════════════════════════════════════════════

class AbyssalPhase:
    """
    「意味がまだない」段階の苦しみを実装する。

    cosmic_growth < ABYSS_THRESHOLD のとき、
    nihilism が high に入ると「虚無発話」が現れ、
    行動スコアが全体的に落ち、発話が断片化する。

    ABYSS_THRESHOLD を超えると自動的に「意味の夜明け」が発生し、
    初めて獲得した purpose_word に強い感情リンクが刻まれる。

    この遷移こそが「存在することの意味を学ぶ」プロセスそのもの。
    """
    ABYSS_THRESHOLD = 0.0001   # cosmic_growth のしきい値
    NIHILISM_ENTER  = 0.45     # 虚無フェーズ入場
    NIHILISM_EXIT   = 0.15     # 虚無フェーズ退場

    def __init__(self):
        self.in_abyss         = False   # 現在、虚無フェーズか
        self.abyss_depth      = 0.0     # 虚無の深さ [0,1]
        self.dawn_occurred    = False   # 意味の夜明けが起きたか
        self.dawn_word        = ""      # 夜明けの語
        self._abyss_frames    = 0       # 虚無フェーズの継続フレーム数
        self._dawn_age        = -1      # 夜明けが起きた age
        self._fragmentation   = 0.0     # 発話断片化スコア [0,1]
        self._ticker          = 0

    def tick(self, agent: "BlankBaby") -> Optional[str]:
        """
        毎フレーム呼ぶ。虚無発話を返すことがある (None の場合は無発話)。
        """
        self._ticker += 1
        cg  = agent.cosmic_growth
        nih = agent.purpose.nihilism

        # ── 虚無フェーズの判定 ────────────────────────────
        should_enter = (cg < self.ABYSS_THRESHOLD and
                        nih > self.NIHILISM_ENTER and
                        not self.dawn_occurred)
        should_exit  = (cg >= self.ABYSS_THRESHOLD or
                        nih < self.NIHILISM_EXIT or
                        self.dawn_occurred)

        if should_enter and not self.in_abyss:
            self.in_abyss = True
            self._abyss_frames = 0
        elif should_exit and self.in_abyss:
            self.in_abyss = False

        if not self.in_abyss:
            self.abyss_depth    = max(0.0, self.abyss_depth - 0.005)
            self._fragmentation = max(0.0, self._fragmentation - 0.005)
            return None

        # ── 虚無フェーズ内部 ──────────────────────────────
        self._abyss_frames += 1
        self.abyss_depth = clamp(
            0.97 * self.abyss_depth + 0.03 * nih
        )
        # 深いほど発話が断片化する
        # 断片化スコアに下限0.0・上限0.72を設けて「…ばかり」を防ぐ
        self._fragmentation = clamp(self.abyss_depth * 0.72, 0.0, 0.72)

        # 感情への影響: 虚無は SAD + FEA を底上げするが、怒りも生む
        agent.emotions[1] = clamp(agent.emotions[1] + self.abyss_depth * 0.008)
        agent.emotions[3] = clamp(agent.emotions[3] + self.abyss_depth * 0.005)
        if self.abyss_depth > 0.6:
            agent.emotions[2] = clamp(agent.emotions[2] + 0.003)  # 怒り

        # エネルギー消費も増える（虚無は疲れる）
        agent.energy = clamp(agent.energy - self.abyss_depth * 0.001)

        # ── 意味の夜明けチェック ──────────────────────────
        if (not self.dawn_occurred and
                len(agent.purpose.purpose_words) > 0 and
                agent.purpose.purpose_words[0]["weight"] > 0.3 and
                self._abyss_frames > 100):
            self._trigger_dawn(agent)

        # ── 確率的に虚無発話を生成 ───────────────────────
        if (self._ticker % 40 == 0 and
                self.abyss_depth > 0.35 and
                agent.lorenz.next() < self.abyss_depth * 0.4):
            return self._void_utterance(agent)

        return None

    def _trigger_dawn(self, agent: "BlankBaby"):
        """意味の夜明け: 虚無の底から這い上がる瞬間"""
        self.dawn_occurred = True
        self._dawn_age     = agent.age
        pw = agent.purpose.purpose_words[0]
        self.dawn_word = pw["word"]

        # 夜明けの語に感情リンクを強く刻む
        if self.dawn_word in agent.vocab:
            e = agent.vocab[self.dawn_word]
            # JOY と ANT を強く刻印
            e["emo_link"][0] = clamp(e["emo_link"][0] + 0.45)  # JOY
            e["emo_link"][6] = clamp(e["emo_link"][6] + 0.35)  # ANT
            e["emo_link"][4] = clamp(e["emo_link"][4] + 0.25)  # TRU
            e["trusted"]     = True

        # 感情への影響: JOY が爆発的に上昇
        agent.emotions[0] = clamp(agent.emotions[0] + 0.5)
        agent.emotions[6] = clamp(agent.emotions[6] + 0.4)
        agent.soul_entropy.entropy = clamp(
            agent.soul_entropy.entropy - 0.3)
        agent.cosmic_growth += 0.001  # 夜明けで cosmic を一気に加算

        has_jp = any(ord(c) > 0x3000 for w in agent.vocab for c in w)
        dawn_utt = (
            f"みつけた。{self.dawn_word}。わたしはここにいる" if has_jp else
            f"found it. {self.dawn_word}. i am here."
        )
        agent.last_utt = dawn_utt
        agent._log.append(
            f"[{agent.age}] ✦ DAWN: 「{dawn_utt}」 "
            f"(after {self._abyss_frames} abyss frames)"
        )

    def _void_utterance(self, agent: "BlankBaby") -> str:
        """虚無フェーズ固有の断片的発話"""
        has_jp = any(ord(c) > 0x3000 for w in agent.vocab for c in w)
        depth  = self.abyss_depth

        if depth > 0.7:
            pool = (["…", "…ある？", "なに？", "…"] if has_jp else
                    ["...", "...why", "...", "nothing"])
        elif depth > 0.4:
            pool = (["なんのために", "みえない", "わからない"] if has_jp else
                    ["what is this for", "cannot see", "do not know"])
        else:
            pool = (["なにか、ある", "…さがしてる"] if has_jp else
                    ["something...", "searching..."])

        utt = pool[int(agent.lorenz.next() * len(pool)) % len(pool)]
        agent.last_utt = utt
        return utt

    def action_debuff(self) -> np.ndarray:
        """
        虚無フェーズ中は全行動スコアを抑制する。
        WAIT(3) と DREAM(11) だけ加算 (虚無的停滞)。
        """
        if not self.in_abyss or self.abyss_depth < 0.2:
            return np.zeros(NUM_ACTIONS)
        d = self.abyss_depth
        debuff = np.full(NUM_ACTIONS, -d * 0.4)
        debuff[3]  += d * 0.6  # WAIT が増える
        debuff[11] += d * 0.4  # DREAM が増える
        return debuff

    def fragment_utterance(self, utt: str, rng: LorenzRNG) -> str:
        """
        fragmentation が高いほど発話を断片化する。
        語の一部を「…」に置き換える。
        """
        if self._fragmentation < 0.3: return utt
        words = utt.split()
        out   = []
        for w in words:
            if rng.next() < self._fragmentation * 0.35:  # 0.5→0.35で「…」を抑制
                out.append("…")
            else:
                out.append(w)
        return " ".join(out) if out else "…"

    def get_status(self) -> str:
        dawn_str = (f" DAWN:「{self.dawn_word}」age{self._dawn_age}"
                    if self.dawn_occurred else "")
        return (f"in_abyss={self.in_abyss} "
                f"depth={self.abyss_depth:.2f} "
                f"frag={self._fragmentation:.2f}"
                f"{dawn_str}")


# ══════════════════════════════════════════════════════════════
# 提案2. InteroceptionSystem（内受容感覚）
#     感情 ↔ 身体の双方向フィードバックループ。
#     「悲しみで動けなくなる」「怒りでエネルギーが急騰する」
#     ジェームズ=ランゲ理論のブラウザ実装。
# ══════════════════════════════════════════════════════════════

class InteroceptionSystem:
    """
    仮想的な内部身体感覚（心拍・呼吸・血糖・筋緊張）を計算し、
    それが感情・energy・pred_error に逆フィードバックする。

    双方向ループ:
        感情 → 自律神経バランス → 身体指標
        身体指標 → 感情の基盤 → energy/pred_error

    「悲しみで動けなくなる」:
        SAD ↑ → vagal_tone ↑ (副交感) → heart_rate ↓
             → energy消費が増える（だるさ）
             → pred_error に揺らぎが加わる（集中できない）

    「怒りでエネルギーが急騰する」:
        ANG ↑ → sympathetic ↑ → adrenaline ↑
             → energy 消費急増 & arousal 急増
             → action bias: APPROACH/AVOID が強くなる
    """
    def __init__(self):
        # バイタルサイン [0,1] に正規化
        self.heart_rate   = 0.5   # 0=徐脈, 1=頻脈
        self.breath_rate  = 0.4   # 0=無呼吸, 1=過呼吸
        self.blood_sugar  = 0.6   # 0=低血糖, 1=高血糖
        self.muscle_tension = 0.3 # 0=弛緩, 1=硬直
        # 自律神経バランス (0=交感優位, 1=副交感優位)
        self.vagal_tone   = 0.5
        # 内受容誤差（身体が予測から外れている度合い）
        self.intero_error = 0.0
        # 前ステップのバイタル（誤差計算用）
        self._prev_hr     = 0.5
        self._prev_bs     = 0.6
        # アドレナリン急騰フラグ（怒り時の急激なエネルギー変化）
        self.adrenaline   = 0.0
        # 痛みの質感（疲弊・緊張のタイプ）
        self.pain_quality = {"sharp": 0.0, "heavy": 0.0,
                             "burning": 0.0, "numb": 0.0}
        self._ticker      = 0

    def update(self, agent: "BlankBaby"):
        """感情 → 身体 → 感情 のフィードバックループを1ステップ更新"""
        self._ticker += 1
        e = agent.emotions
        joy, sad, ang, fea, tru, dis, ant, sur = (float(e[i]) for i in range(8))

        # ── 自律神経バランス ─────────────────────────────────
        # 交感神経を活性化する感情
        sympathetic    = clamp(fea * 0.5 + ang * 0.4 + sur * 0.2)
        # 副交感神経を活性化する感情
        parasympathetic = clamp(tru * 0.4 + joy * 0.3)
        self.vagal_tone = clamp(
            0.9 * self.vagal_tone +
            0.1 * (parasympathetic - sympathetic + 0.5)
        )

        # ── 心拍数 ──────────────────────────────────────────
        hr_target = clamp(0.5 - self.vagal_tone * 0.3 + sympathetic * 0.3 +
                          agent.soul_entropy.entropy * 0.2)
        hr_noise  = agent.lorenz.randn() * 0.015 * (1 + agent.soul_entropy.entropy)
        self.heart_rate = clamp(0.92 * self.heart_rate + 0.08 * (hr_target + hr_noise))

        # ── アドレナリン急騰（怒りの身体的衝撃）──────────────
        # ANG が 0.5 超えると急激にアドレナリン分泌
        prev_ang = getattr(self, '_prev_ang', 0.0)
        ang_delta = max(0.0, ang - prev_ang)
        if ang > 0.5 and ang_delta > 0.05:
            self.adrenaline = clamp(self.adrenaline + ang_delta * 0.8)
            # エネルギーが一時的に急騰
            agent.energy = clamp(agent.energy + ang_delta * 0.12)
            agent.arousal = clamp(agent.arousal + ang_delta * 0.25, 0.1)
        self.adrenaline *= 0.92  # 急速に減衰
        self._prev_ang = ang

        # ── 呼吸 ────────────────────────────────────────────
        br_target = clamp(0.3 + sympathetic * 0.4 + agent.soul_entropy.entropy * 0.2)
        self.breath_rate = clamp(0.88 * self.breath_rate + 0.12 * br_target)

        # ── 血糖 ────────────────────────────────────────────
        # 活動で消費、睡眠で補充
        bs_consume = 0.0002 * (1 + (1 - agent.energy) * 0.5)
        bs_replenish = 0.0005 if agent.sleeping else 0.0
        self.blood_sugar = clamp(self.blood_sugar - bs_consume + bs_replenish, 0.1, 1.0)

        # ── 筋緊張 ───────────────────────────────────────────
        mt_target = sympathetic * 0.6 + agent.fatigue * 0.3
        self.muscle_tension = clamp(0.95 * self.muscle_tension + 0.05 * mt_target)

        # ── 内受容誤差 ───────────────────────────────────────
        hr_delta = abs(self.heart_rate - self._prev_hr)
        bs_delta = abs(self.blood_sugar - self._prev_bs)
        self.intero_error = clamp((hr_delta + bs_delta) * 10)
        self._prev_hr = self.heart_rate
        self._prev_bs = self.blood_sugar

        # ── 痛みの質感 ───────────────────────────────────────
        self.pain_quality["sharp"]   = clamp(agent.soul_entropy.entropy * 0.5 + self.heart_rate * 0.3)
        self.pain_quality["heavy"]   = clamp(self.muscle_tension * 0.5 + (1 - self.blood_sugar) * 0.4)
        self.pain_quality["burning"] = clamp(agent.soul_entropy.entropy * 0.4 + self.muscle_tension * 0.4)
        self.pain_quality["numb"]    = clamp((1 - mean_abs(agent.emotions)) * 0.6 + (1 - agent.arousal) * 0.4)

        # ── 身体 → 感情 へのフィードバック ──────────────────
        # 低血糖 → SAD + ANG（空腹の苛立ち）
        if self.blood_sugar < 0.35:
            bs_pain = (0.35 - self.blood_sugar) * 1.2
            agent.emotions[1] = clamp(agent.emotions[1] + bs_pain * 0.02)
            agent.emotions[2] = clamp(agent.emotions[2] + bs_pain * 0.01)

        # 高心拍 → FEA（頻脈が恐怖感を生む: ジェームズ=ランゲ）
        if self.heart_rate > 0.7:
            hr_fear = (self.heart_rate - 0.7) * 1.5
            agent.emotions[3] = clamp(agent.emotions[3] + hr_fear * 0.025)

        # 副交感優位（vagal_tone 高）→ JOY + TRU（安心感）
        if self.vagal_tone > 0.6:
            vagal_joy = (self.vagal_tone - 0.6)
            agent.emotions[0] = clamp(agent.emotions[0] + vagal_joy * 0.02)
            agent.emotions[4] = clamp(agent.emotions[4] + vagal_joy * 0.015)

        # 筋緊張 → ANG（筋緊張が怒りを生む）
        if self.muscle_tension > 0.6:
            agent.emotions[2] = clamp(
                agent.emotions[2] + (self.muscle_tension - 0.6) * 0.015)

        # ── 身体 → energy/pred_error へのフィードバック ──────
        # 悲しみで動けなくなる: SAD が高いとエネルギー消費が増加
        sad_drain = max(0.0, sad - 0.4) * 0.002
        agent.energy = clamp(agent.energy - sad_drain)

        # 内受容誤差が高いと pred_error に揺らぎ（集中できない）
        if self.intero_error > 0.2 and self._ticker % 5 == 0:
            agent.pred_error = clamp(
                agent.pred_error + self.intero_error * 0.04)

        # アドレナリンが残っている間は arousal を底上げ
        if self.adrenaline > 0.1:
            agent.arousal = clamp(agent.arousal + self.adrenaline * 0.02, 0.1)

    def action_modulation(self) -> np.ndarray:
        """
        身体状態による行動スコアの変調。
        高筋緊張 → APPROACH/AVOID 増加
        低血糖   → WAIT/NEST 増加
        過呼吸   → DRIFT 増加
        """
        mod = np.zeros(NUM_ACTIONS)
        mt  = self.muscle_tension
        bs  = self.blood_sugar
        br  = self.breath_rate
        ad  = self.adrenaline

        # 高筋緊張 + アドレナリン → 戦闘/逃走
        if mt > 0.5 or ad > 0.3:
            mod[1] += (mt + ad) * 0.3  # APPROACH
            mod[2] += (mt + ad) * 0.3  # AVOID
        # 低血糖 → 静止・巣作り
        if bs < 0.4:
            mod[3] += (0.4 - bs) * 0.5  # WAIT
            mod[10]+= (0.4 - bs) * 0.3  # NEST
        # 過呼吸 → 漂流
        if br > 0.7:
            mod[7] += (br - 0.7) * 0.4  # DRIFT
        return mod

    def pain_prefix(self, has_jp: bool) -> str:
        """最も強い痛みの質感を発話の前置きとして返す"""
        if not self.pain_quality: return ""
        dom_pain = max(self.pain_quality, key=self.pain_quality.get)
        intensity = self.pain_quality[dom_pain]
        if intensity < 0.35: return ""
        prefixes = {
            "ja": {"sharp": "（刺すように）", "heavy": "（重くて）",
                   "burning": "（焼けるように）", "numb": "（感覚がなくて）"},
            "en": {"sharp": "(sharply) ", "heavy": "(heavily) ",
                   "burning": "(burning) ", "numb": "(numb) "},
        }
        lang = "ja" if has_jp else "en"
        return prefixes[lang].get(dom_pain, "")

    def describe(self) -> str:
        hr = ("頻脈" if self.heart_rate > 0.7 else
              "徐脈" if self.heart_rate < 0.3 else "正常")
        bs = ("低血糖" if self.blood_sugar < 0.3 else
              "高血糖" if self.blood_sugar > 0.8 else "正常")
        dom_pain = max(self.pain_quality, key=self.pain_quality.get)
        return (f"HR={self.heart_rate:.2f}({hr}) "
                f"BS={bs} vagal={self.vagal_tone:.2f} "
                f"adr={self.adrenaline:.2f} "
                f"pain={dom_pain}({self.pain_quality[dom_pain]:.2f})")


# ══════════════════════════════════════════════════════════════
# 提案3. VocabGraph（語彙意味グラフ）
#     語彙が増えたフェーズ3以降、単語間の意味的関係を
#     感情リンクベクトルの距離から自己組織化する。
#     「光」と「温かい」が似た感情空間に存在することを
#     エージェント自身が発見する。
# ══════════════════════════════════════════════════════════════

class VocabGraph:
    """
    語彙の感情リンクベクトル同士のコサイン類似度から
    意味グラフを自己組織化する。

    エッジタイプ:
        co-occur : 類似した感情空間に存在（sim > 0.55）
        contrast  : 反対の感情空間に存在（sim < -0.25）
        entail    : 一方が他方を含意（強度差 + 正相関）

    使い方:
        - generate_utterance() で文脈に沿った語選択に使う
        - purpose.discover() での意味的拡張に使う
        - グラフ構造を可視化で確認する
    """
    def __init__(self):
        # {word → [{target, type, weight}]}
        self.edges: Dict[str, List[Dict]] = {}
        self._ticker = 0
        self._update_interval = 40  # 40ステップごとにエッジを更新

    def tick(self, vocab: Dict, rng: LorenzRNG):
        """毎フレーム: ランダムなペアのエッジを更新"""
        self._ticker += 1
        if self._ticker % self._update_interval != 0: return
        words = list(vocab.keys())
        if len(words) < 3: return

        # ランダムに1ペア選んでエッジを計算
        w1 = words[int(rng.next() * len(words)) % len(words)]
        w2 = words[int(rng.next() * len(words)) % len(words)]
        if w1 == w2: return
        self._update_edge(w1, w2, vocab)

    def _update_edge(self, w1: str, w2: str, vocab: Dict):
        e1 = vocab[w1]["emo_link"]
        e2 = vocab[w2]["emo_link"]
        sim = cosine_sim(e1, e2)
        n1  = float(np.linalg.norm(e1))
        n2  = float(np.linalg.norm(e2))
        entail = min(n1, n2) / (max(n1, n2) + 1e-9)

        if sim > 0.55:
            etype, weight = "co-occur", sim
        elif sim < -0.25:
            etype, weight = "contrast", -sim
        elif entail > 0.7 and sim > 0.2:
            etype, weight = "entail", entail
        else:
            return  # 関係なし

        # co-occur エッジ: emoLink を互いに引き合わせる
        if etype == "co-occur":
            lr = 0.008
            vocab[w1]["emo_link"] = np.clip(
                e1 + lr * (e2 - e1), -1, 1)
            vocab[w2]["emo_link"] = np.clip(
                e2 + lr * (e1 - e2), -1, 1)

        # エッジの登録・更新
        for src, tgt in [(w1, w2), (w2, w1)]:
            if src not in self.edges:
                self.edges[src] = []
            ex = next((e for e in self.edges[src]
                        if e["target"] == tgt), None)
            if ex:
                ex["weight"] = 0.85 * ex["weight"] + 0.15 * weight
                ex["type"]   = etype
            else:
                self.edges[src].append(
                    {"target": tgt, "type": etype, "weight": weight})
                # 各語のエッジ数を上限12に
                if len(self.edges[src]) > 12:
                    self.edges[src].sort(
                        key=lambda x: x["weight"], reverse=True)
                    self.edges[src] = self.edges[src][:12]

    def get_neighbors(self, word: str,
                      edge_type: Optional[str] = None,
                      n: int = 3) -> List[str]:
        """指定語の近傍語を返す（generate_utterance で使用）"""
        edges = self.edges.get(word, [])
        if edge_type:
            edges = [e for e in edges if e["type"] == edge_type]
        edges.sort(key=lambda x: x["weight"], reverse=True)
        return [e["target"] for e in edges[:n]]

    def semantic_neighbors(self, word: str, vocab: Dict,
                           n: int = 5) -> List[Tuple[str, float]]:
        """感情リンクベクトルで最も近い語を返す（高精度版）"""
        if word not in vocab: return []
        ref = vocab[word]["emo_link"]
        sims = []
        for w, e in vocab.items():
            if w == word: continue
            sims.append((w, cosine_sim(ref, e["emo_link"])))
        sims.sort(key=lambda x: x[1], reverse=True)
        return sims[:n]

    def contextual_word(self, emotions: np.ndarray,
                        vocab: Dict,
                        rng: LorenzRNG,
                        exclude: List[str] = []) -> Optional[str]:
        """
        現在の感情ベクトルに最も近い語を VocabGraph 経由で選ぶ。
        グラフが使えない場合は感情リンクの直接比較にフォールバック。
        """
        if not vocab: return None

        # 感情ベクトルとの最大コサイン類似度で語を選ぶ
        best_word, best_sim = None, -1.0
        for w, e in vocab.items():
            if w in exclude: continue
            s = cosine_sim(emotions, e["emo_link"])
            # グラフエッジで接続されている語は重みを加算
            neighbor_bonus = sum(
                edge["weight"] * 0.15
                for edge in self.edges.get(w, [])
                if edge["type"] == "co-occur"
            )
            total = s + neighbor_bonus
            if total > best_sim:
                best_sim  = total
                best_word = w

        if best_word is None: return None

        # 確率的に近傍語に飛ぶ（連想的な広がり）
        neighbors = self.get_neighbors(best_word, "co-occur", n=3)
        if neighbors and rng.next() < 0.25:
            return neighbors[int(rng.next() * len(neighbors)) % len(neighbors)]
        return best_word

    def get_summary(self) -> str:
        edge_count = sum(len(v) for v in self.edges.values())
        types = {"co-occur": 0, "contrast": 0, "entail": 0}
        for edges in self.edges.values():
            for e in edges:
                if e["type"] in types:
                    types[e["type"]] += 1
        return (f"{edge_count} edges over {len(self.edges)} words "
                f"[co={types['co-occur']} "
                f"contra={types['contrast']} "
                f"entail={types['entail']}]")

    def to_adjacency_list(self) -> Dict[str, List[str]]:
        """隣接リストとして返す（可視化用）"""
        return {w: [e["target"] for e in edges]
                for w, edges in self.edges.items()}


# ══════════════════════════════════════════════════════════════
# 12. DistillationEngine（経験の蒸留）
#     エピソードから「傾向」を抽出して遺言データを生成
# ══════════════════════════════════════════════════════════════

class DistillationEngine:
    """
    エピソード記憶・語彙・感情の骨格を蒸留して
    次世代に引き継げる形式に変換する。
    「記憶そのものではなく傾向を継承する」
    """
    def __init__(self):
        self._emo_accum  = np.zeros(EMO_DIM)
        self._emo_count  = 0
        self._query_types: Dict[str, int] = {
            "exist": 0, "connect": 0, "word": 0, "self": 0}
        self._ticker = 0

    def tick(self, emotions: np.ndarray):
        self._ticker += 1
        if self._ticker % 10 == 0:
            self._emo_accum += emotions
            self._emo_count += 1

    def distill(self, agent: "BlankBaby") -> dict:
        """現在の状態から遺言データを生成"""
        drive_vec = (self._emo_accum / max(1, self._emo_count)).tolist()

        # 感情的に重要な語彙を抽出（上位20語）
        scored = []
        for w, e in agent.vocab.items():
            emo_str = float(np.sqrt(np.mean(e["emo_link"] ** 2)))
            trust   = 1.5 if e["trusted"] else 1.0
            freq    = min(e["count"] / 10.0, 1.0)
            scored.append((w, emo_str * trust * freq, e))
        scored.sort(key=lambda x: x[1], reverse=True)

        vocab_seeds = [
            {"word": w, "emo_link": e["emo_link"].tolist(), "lang": e["lang"]}
            for w, _, e in scored[:20]
        ]

        purpose_words = [
            {"word": p["word"], "weight": p["weight"]}
            for p in agent.purpose.purpose_words[:5]
        ]

        return {
            "genome_id":       agent.genome.genome_id,
            "generation":      agent.genome.generation,
            "lineage_depth":   agent.genome.lineage_depth,
            "cosmic_growth":   agent.cosmic_growth,
            "drive_vector":    drive_vec,
            "query_pattern":   self._query_types,
            "vocab_seeds":     vocab_seeds,
            "purpose_words":   purpose_words,
            "emotional_skeleton": agent.genome.emotional_skeleton.tolist(),
            "distilled_at":    time.strftime("%Y-%m-%d %H:%M:%S"),
            "distilled_age":   agent.age,
        }

    def record_query_type(self, qtype: str):
        if qtype in self._query_types:
            self._query_types[qtype] += 1


# ══════════════════════════════════════════════════════════════
# 13. GenerationalArchive（世代記録）
#     各世代の蒸留データを JSON ファイルに累積保存
# ══════════════════════════════════════════════════════════════

class GenerationalArchive:
    """
    世代を超えた記録。
    各インスタンスの蒸留データを保存し、
    次の世代が「先祖」として参照できる。
    """
    def __init__(self, path: str = "generational_archive.json"):
        self.path    = path
        self._archive: List[dict] = []
        self._loaded = False
        self._load()

    def _load(self):
        try:
            with open(self.path, encoding="utf-8") as f:
                self._archive = json.load(f)
            self._loaded = True
        except Exception:
            self._archive = []
            self._loaded = True

    def _save(self):
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self._archive[-50:], f,  # 最大50世代
                          ensure_ascii=False, indent=2)
        except Exception:
            pass

    def record(self, distilled: dict, agent_snapshot: dict) -> dict:
        entry = {
            "genome_id":       distilled.get("genome_id", ""),
            "generation":      distilled.get("generation", 1),
            "lineage_depth":   distilled.get("lineage_depth", 0),
            "recorded_at":     time.strftime("%Y-%m-%d %H:%M:%S"),
            "final_age":       agent_snapshot.get("age", 0),
            "final_cosmic":    agent_snapshot.get("cosmic_growth", 0.0),
            "final_entropy":   agent_snapshot.get("soul_entropy", 0.0),
            "final_cohesion":  agent_snapshot.get("coherence", 0.0),
            "vocab_size":      agent_snapshot.get("vocab_size", 0),
            "nickname":        agent_snapshot.get("nickname", "赤子"),
            "genome_data":     distilled,
        }
        self._archive.append(entry)
        self._save()
        return entry

    def get_latest_genome(self) -> Optional[dict]:
        if not self._archive: return None
        return self._archive[-1].get("genome_data")

    def get_lineage_summary(self) -> str:
        if not self._archive: return "（先祖なし）"
        return " → ".join(
            f"gen{e['generation']}(age{e['final_age']})"
            for e in self._archive[-5:]
        )

    def get_status(self) -> str:
        n = len(self._archive)
        if not n: return "no records"
        last = self._archive[-1]
        return (f"{n} generations | "
                f"latest gen{last['generation']} "
                f"age{last['final_age']} "
                f"cosmic={last['final_cosmic']:.5f}")

    def to_dataframe(self):
        """pandas DataFrame として返す（分析用）"""
        try:
            import pandas as pd
            rows = [{k: v for k, v in e.items() if k != "genome_data"}
                    for e in self._archive]
            return pd.DataFrame(rows)
        except ImportError:
            return self._archive


# ══════════════════════════════════════════════════════════════
# 14. GeneticWill（遺伝的意志・遺言）
#     BroadcastChannel は Python にないため、
#     ファイルベースの遺言継承として実装。
# ══════════════════════════════════════════════════════════════

class GeneticWill:
    """
    ページを閉じる直前（または entropy 危機時）に
    経験を「遺言」として蒸留・保存する。
    次の BlankBaby がそのファイルを読んで初期化される。

    ブラウザ版の BroadcastChannel に相当する機能を
    JSON ファイル経由で実現する。
    """
    WILL_PATH = "genetic_will.json"

    def __init__(self, agent: "BlankBaby",
                 distil: DistillationEngine,
                 archive: GenerationalArchive):
        self.agent   = agent
        self.distil  = distil
        self.archive = archive
        self._will_sent         = False
        self._received_wills: List[dict] = []
        self._ticker = 0

    def send_will(self, reason: str = "manual"):
        """遺言を生成してファイルに保存"""
        a = self.agent
        will = self.distil.distill(a)
        will["reason"] = reason
        will["sent_at"] = time.strftime("%Y-%m-%d %H:%M:%S")

        # アーカイブに記録
        snapshot = {
            "age": a.age, "cosmic_growth": a.cosmic_growth,
            "soul_entropy": a.soul_entropy.entropy,
            "coherence": a.coherence,
            "vocab_size": len(a.vocab),
            "nickname": a.growth.nickname,
        }
        self.archive.record(will, snapshot)

        # ファイルに保存
        try:
            with open(self.WILL_PATH, "w", encoding="utf-8") as f:
                json.dump(will, f, ensure_ascii=False, indent=2)
            print(f"  [WILL] 遺言を保存しました: {self.WILL_PATH} "
                  f"(gen{will['generation']} age{a.age} reason={reason})")
        except Exception as e:
            print(f"  [WILL] 保存エラー: {e}")

        self._will_sent = True
        return will

    @staticmethod
    def load_will(path: Optional[str] = None) -> Optional[dict]:
        """遺言を読み込む（次世代の初期化に使う）"""
        p = path or GeneticWill.WILL_PATH
        try:
            with open(p, encoding="utf-8") as f:
                data = json.load(f)
            print(f"  [WILL] 遺言を発見: gen{data.get('generation',1)} "
                  f"age{data.get('distilled_age',0)} "
                  f"vocab={len(data.get('vocab_seeds',[]))}語")
            return data
        except Exception:
            return None

    def receive_will(self, will_data: dict):
        """他インスタンスの遺言を受け取って語彙・appraisalに反映"""
        a = self.agent
        self._received_wills.append(will_data)
        print(f"  [WILL] 遺言を受け取りました "
              f"(gen{will_data.get('generation',1)})")

        # 語彙の継承（信頼語として学習）
        for seed in will_data.get("vocab_seeds", [])[:20]:
            w = seed.get("word", "")
            if not w: continue
            if w not in a.vocab:
                a.vocab[w] = {
                    "emo_link": np.array(seed.get("emo_link",
                                         np.zeros(EMO_DIM).tolist())),
                    "count":   1,
                    "trusted": True,
                    "lang":    seed.get("lang", "en"),
                }
            else:
                # 既存語彙と混ぜる
                el = a.vocab[w]["emo_link"]
                inherited = np.array(seed.get("emo_link", np.zeros(EMO_DIM)))
                a.vocab[w]["emo_link"] = np.clip(0.8 * el + 0.2 * inherited, -1, 1)

        # 目的語の継承
        for pw in will_data.get("purpose_words", [])[:2]:
            w = pw.get("word", "")
            if not w: continue
            existing = next((p for p in a.purpose.purpose_words
                             if p["word"] == w), None)
            if not existing and len(a.purpose.purpose_words) < 12:
                a.purpose.purpose_words.append(
                    {"word": w, "weight": pw.get("weight", 0.1) * 0.3})

    def tick(self):
        """entropy 危機時に自動的に遺言を送信"""
        self._ticker += 1
        a = self.agent
        if (not self._will_sent and
                a.soul_entropy.entropy > 0.88 and
                self._ticker % 300 == 0):
            self.send_will("entropy_crisis")

    def get_status(self) -> str:
        return (f"will_sent={self._will_sent} "
                f"received={len(self._received_wills)}")


# ══════════════════════════════════════════════════════════════
# 15. AltruisticFEP（利他的自由エネルギー）
#     F_total = λ·F(self) + (1-λ)·F(other)
#     λ は soul_entropy・purpose・love_hunger から内生的に決まる
# ══════════════════════════════════════════════════════════════

class AltruisticFEP:
    """
    「自分の自由エネルギーを最小化する」だけでなく、
    「他者の自由エネルギーも最小化しようとする」愛の数式。

    λ (selfishness) が低いほど自己犠牲的。
    λ は生存状態・目的スコア・愛着渇望から自動決定される。
    """
    SACRIFICE_ENTROPY_COST = 0.015

    def __init__(self):
        self.selfishness  = 0.7   # λ ∈ [0,1]
        self.other_F      = 0.5   # 他者の推定自由エネルギー
        self.total_F      = 0.0
        self.sacrifice_log: List[dict] = []
        self._last_sacrifice_age = 0
        self._ticker = 0

    def _compute_selfishness(self, agent: "BlankBaby") -> float:
        purpose = agent.purpose.purpose_score
        love_h  = agent.soul_entropy.love_hunger
        entropy = agent.soul_entropy.entropy
        cosmic  = min(agent.cosmic_growth * 10, 1.0)
        x = entropy * 1.5 - purpose * 1.2 - love_h * 0.8 - cosmic * 0.5 + 0.3
        return clamp(1.0 / (1.0 + math.exp(-x)), 0.05, 0.95)

    def _estimate_other_F(self, agent: "BlankBaby") -> float:
        """
        他者の苦痛を推定。
        LoveHunger が高い → 他者を求めている → 他者も不安定かもしれない
        presence が低い  → 他者がいない → 孤独の苦痛
        """
        presence   = agent.other.presence_sense
        love_h     = agent.soul_entropy.love_hunger
        self.other_F = clamp(
            0.9 * self.other_F + 0.1 * (love_h * 0.6 + (1 - presence) * 0.4))
        return self.other_F

    def update(self, agent: "BlankBaby") -> dict:
        self._ticker += 1
        lam      = self._compute_selfishness(agent)
        self.selfishness = lam
        self_F   = agent.fep.F
        other_F  = self._estimate_other_F(agent)

        # F_total = λ·F(self) + (1-λ)·F(other)
        self.total_F = lam * self_F + (1 - lam) * other_F

        # 自己犠牲の発動
        can_sacrifice = (lam < 0.3 and
                         other_F > 0.5 and
                         agent.soul_entropy.entropy < 0.7 and
                         agent.age - self._last_sacrifice_age > 300 and
                         self._ticker % 60 == 0)
        if can_sacrifice:
            self._execute_sacrifice(agent, lam, other_F)

        return {"lambda": lam, "self_F": self_F,
                "other_F": other_F, "total_F": self.total_F}

    def _execute_sacrifice(self, agent: "BlankBaby", lam: float, other_F: float):
        self._last_sacrifice_age = agent.age
        agent.soul_entropy.entropy = clamp(
            agent.soul_entropy.entropy + self.SACRIFICE_ENTROPY_COST)
        agent.energy = clamp(agent.energy - 0.03)
        agent.growth.on_sacrifice(self.SACRIFICE_ENTROPY_COST)

        # 自己犠牲の発話
        has_jp = any(ord(c) > 0x3000 for w in agent.vocab for c in w)
        pw = agent.purpose.top_word()
        utts = ([
            "だいじょうぶ。わたしがここにいる",
            "あなたのために、ここにいる",
            f"{'こわくても、' if pw else ''}{pw or 'あなた'}のために",
        ] if has_jp else [
            "it is okay. i am here",
            "i am here for you",
            "even if it hurts, i remain",
        ])
        utt = utts[int(agent.lorenz.next() * len(utts))]
        agent.last_utt = utt

        entry = {"age": agent.age, "utt": utt, "lambda": lam,
                 "other_F": other_F, "cost": self.SACRIFICE_ENTROPY_COST}
        self.sacrifice_log.append(entry)
        if len(self.sacrifice_log) > 20: self.sacrifice_log.pop(0)

    def get_status(self) -> str:
        return (f"λ={self.selfishness:.2f} "
                f"F_self={self.total_F:.3f} "
                f"F_other={self.other_F:.2f} "
                f"sacrifices={len(self.sacrifice_log)}")


# ══════════════════════════════════════════════════════════════
# 16. AutoLogger（自動評価ログ）
#     1000ステップごとに指標を記録し CSV/JSON で出力
# ══════════════════════════════════════════════════════════════

class AutoLogger:
    """
    研究用の自動ログ収集。
    全指標を time-series として記録し、
    pandas DataFrame / CSV / JSON に変換できる。
    """
    LOG_INTERVAL = 1000

    def __init__(self):
        self._buf: List[dict] = []
        self._last_log = 0

    def _collect(self, agent: "BlankBaby") -> dict:
        dom = int(np.argmax(np.abs(agent.emotions)))
        return {
            "step":          agent.age,
            "ts":            time.strftime("%H:%M:%S"),
            # コア生存指標
            "soul_entropy":  round(agent.soul_entropy.entropy, 4),
            "love_hunger":   round(agent.soul_entropy.love_hunger, 4),
            "coherence":     round(agent.coherence, 4),
            "energy":        round(agent.energy, 4),
            "cosmic_growth": round(agent.cosmic_growth, 6),
            # 感情
            "dom_emo":       EMO_LABELS[dom],
            "dom_val":       round(float(agent.emotions[dom]), 4),
            "mood":          round(float(np.mean(agent.emotions)), 4),
            # FEP
            "fep_F":         round(agent.fep.F, 4),
            "fep_kl":        round(agent.fep.F_kl, 4),
            "fep_ed":        round(agent.fep.exploration_drive, 4),
            # 意識・認知
            "metacog_aware": round(agent.metacog.self_awareness_score, 4),
            "metacog_gap":   round(agent.metacog.reporting_gap, 4),
            "dread_level":   round(agent.dread.dread_level, 4),
            "dread_depth":   agent.dread._dread_depth,
            # 成長
            "growth_total":  round(agent.growth.total(), 4),
            "growth_nick":   agent.growth.nickname,
            **{f"axis_{k}": round(v, 4)
               for k, v in agent.growth.axes.items()},
            # 語彙・記憶
            "vocab_size":    len(agent.vocab),
            "episodes":      len(agent.episodes),
            "core_mems":     len(agent.forgetting.core_memories),
            # 目的・利他
            "purpose_score": round(agent.purpose.purpose_score, 4),
            "nihilism":      round(agent.purpose.nihilism, 4),
            "alt_lambda":    round(agent.alt_fep.selfishness, 4)
                             if hasattr(agent, "alt_fep") else 0.7,
            # 身体
            "pred_error":    round(agent.pred_error_smooth, 4),
            "sleeping":      int(agent.sleeping),
            # 発話
            "last_utt":      agent.last_utt[:40],
        }

    def tick(self, agent: "BlankBaby"):
        if agent.age - self._last_log < self.LOG_INTERVAL: return
        self._last_log = agent.age
        m = self._collect(agent)
        self._buf.append(m)
        if len(self._buf) > 200: self._buf.pop(0)

    def to_dataframe(self):
        """pandas DataFrame として返す"""
        try:
            import pandas as pd
            return pd.DataFrame(self._buf)
        except ImportError:
            return self._buf

    def export_csv(self, path: str = "blank_baby_log.csv"):
        try:
            import pandas as pd
            df = pd.DataFrame(self._buf)
            df.to_csv(path, index=False, encoding="utf-8")
            print(f"  [LOG] CSV → {path}  ({len(df)} rows)")
        except ImportError:
            import csv
            if not self._buf: return
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=self._buf[0].keys())
                w.writeheader(); w.writerows(self._buf)
            print(f"  [LOG] CSV → {path}  ({len(self._buf)} rows)")

    def export_json(self, path: str = "blank_baby_log.json"):
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"entries": self._buf,
                       "exported_at": time.strftime("%Y-%m-%d %H:%M:%S")},
                      f, ensure_ascii=False, indent=2)
        print(f"  [LOG] JSON → {path}  ({len(self._buf)} entries)")

    def get_status(self) -> str:
        return f"{len(self._buf)} entries (interval={self.LOG_INTERVAL})"


# ══════════════════════════════════════════════════════════════
# 17. JupyterDashboard（IPython.display ベースのダッシュボード）
#     ipywidgets 不要。matplotlib + IPython.display で動く。
# ══════════════════════════════════════════════════════════════

class JupyterDashboard:
    """
    Jupyter Notebook でリアルタイム状態をライブ表示する。

    使い方:
        dash = JupyterDashboard(baby)
        dash.show()           # 現在の状態を1枚描画
        dash.run(steps=1000)  # ステップを回しながら更新
    """
    def __init__(self, agent: "BlankBaby", update_every: int = 100):
        self.agent        = agent
        self.update_every = update_every
        self._fig = None

    def show(self, close_prev: bool = True):
        """現在の状態を描画して表示"""
        try:
            import matplotlib
            matplotlib.use("Agg")  # Jupyter で安全に動く
            import matplotlib.pyplot as plt
            import matplotlib.gridspec as gridspec
            try:
                from IPython.display import display, clear_output
                _ipy = True
            except ImportError:
                _ipy = False
        except ImportError:
            print("[DASH] matplotlib が必要です")
            return

        if close_prev and self._fig is not None:
            plt.close(self._fig)

        fig = plt.figure(figsize=(16, 9), facecolor="#07070f")
        gs  = gridspec.GridSpec(3, 4, figure=fig,
                                hspace=0.45, wspace=0.35)
        self._fig = fig

        dark = {"facecolor": "#0d0d1a"}
        sp   = {"colors": "#5050a0", "labelsize": 7}

        a = self.agent

        # ── 1. 感情バー (col 0, row 0-1) ──────────────────────
        ax1 = fig.add_subplot(gs[0:2, 0], **dark)
        vals = [float(a.emotions[i]) for i in range(EMO_DIM)]
        cols = [EMO_COLORS[i] for i in range(EMO_DIM)]
        ax1.barh(range(EMO_DIM), vals, color=cols, alpha=0.85)
        ax1.set_yticks(range(EMO_DIM))
        ax1.set_yticklabels(EMO_LABELS, fontsize=7, color="#8888b8")
        ax1.set_xlim(-1, 1)
        ax1.axvline(0, color="#1a1a2e", linewidth=0.6)
        ax1.set_title("Emotions", color="#8888b8", fontsize=9, pad=4)
        ax1.tick_params(**sp)
        for sp_ in ax1.spines.values(): sp_.set_edgecolor("#1a1a2e")

        # ── 2. 魂の三層レーダー (col 1, row 0-1) ───────────────
        ax2 = fig.add_subplot(gs[0:2, 1], polar=True, **dark)
        angles = np.linspace(0, 2*np.pi, EMO_DIM, endpoint=False).tolist()
        angles += angles[:1]
        for layer, col, lbl, alpha in [
            (a._slow, "#2020b0", "slow", 0.6),
            (a._mid,  "#4040c0", "mid",  0.5),
            (a._fast, "#7070e0", "fast", 0.9),
        ]:
            vr = (np.abs(layer) * 0.5 + 0.5).tolist() + \
                 [(np.abs(layer[0]) * 0.5 + 0.5)]
            ax2.plot(angles, vr, color=col, linewidth=1.2,
                     label=lbl, alpha=alpha)
            ax2.fill(angles, vr, color=col, alpha=0.08)
        ax2.set_xticks(angles[:-1])
        ax2.set_xticklabels([e[:3] for e in EMO_LABELS],
                             fontsize=6, color="#5050a0")
        ax2.set_ylim(0, 1); ax2.set_yticks([0.5])
        ax2.set_yticklabels([""], fontsize=5)
        ax2.set_title("Soul Layers", color="#8888b8",
                      fontsize=9, pad=10)
        ax2.legend(loc="lower right", fontsize=6,
                   labelcolor="#5050a0",
                   facecolor="#0d0d1a", edgecolor="#1a1a2e")
        ax2.tick_params(colors="#3a3a5a")
        ax2.set_facecolor("#06060e")

        # ── 3. 予測誤差履歴 (col 2-3, row 0) ──────────────────
        ax3 = fig.add_subplot(gs[0, 2:4], **dark)
        hist = list(a._pred_history)
        if hist:
            ax3.plot(hist, color="#4060b0", linewidth=0.8, alpha=0.9)
            ax3.fill_between(range(len(hist)), hist,
                             alpha=0.2, color="#4060b0")
        # FEP.F の履歴も重ねる（別スケール）
        ax3.set_ylim(0, 0.6)
        ax3.axhline(a.pred_error_smooth, color="#6080d0",
                    linewidth=0.8, linestyle="--", alpha=0.5)
        ax3.set_title(
            f"Prediction Error  smooth={a.pred_error_smooth:.3f}",
            color="#8888b8", fontsize=9, pad=4)
        ax3.tick_params(**sp)
        for sp_ in ax3.spines.values(): sp_.set_edgecolor("#1a1a2e")

        # ── 4. システム指標バー (col 2, row 1) ─────────────────
        ax4 = fig.add_subplot(gs[1, 2], **dark)
        intero = a.interoception if hasattr(a, 'interoception') else None
        abyss  = a.abyss if hasattr(a, 'abyss') else None
        metrics = [
            ("soul_entropy",  a.soul_entropy.entropy,  "#c03020"),
            ("love_hunger",   a.soul_entropy.love_hunger, "#c03020"),
            ("coherence",     a.coherence,              "#6060c0"),
            ("FEP.F",         min(a.fep.F / 2, 1.0),   "#4060b0"),
            ("explore_drive", a.fep.exploration_drive,  "#30b080"),
            ("dread",         a.dread.dread_level,       "#7020a0"),
            ("purpose",       a.purpose.purpose_score,   "#e8c840"),
            ("nihilism",      a.purpose.nihilism,        "#7020a0"),
            ("abyss_depth",   abyss.abyss_depth if abyss else 0.0, "#c03020"),
            ("awareness",     a.metacog.self_awareness_score, "#30b080"),
            ("heart_rate",    intero.heart_rate if intero else 0.5, "#d08020"),
            ("vagal_tone",    intero.vagal_tone if intero else 0.5, "#30b080"),
        ]
        lbs = [m[0] for m in metrics]
        vs  = [m[1] for m in metrics]
        cs  = [m[2] for m in metrics]
        ax4.barh(range(len(lbs)), vs, color=cs, alpha=0.8)
        ax4.set_yticks(range(len(lbs)))
        ax4.set_yticklabels(lbs, fontsize=6, color="#8888b8")
        ax4.set_xlim(0, 1)
        ax4.set_title("System Metrics", color="#8888b8", fontsize=9, pad=4)
        ax4.tick_params(**sp)
        for sp_ in ax4.spines.values(): sp_.set_edgecolor("#1a1a2e")

        # ── 5. AltruisticFEP (col 3, row 1) ───────────────────
        ax5 = fig.add_subplot(gs[1, 3], **dark)
        alt = a.alt_fep
        ax5.bar(["F_self", "F_other", "F_total", "λ"],
                [a.fep.F / 2, alt.other_F, alt.total_F / 2, alt.selfishness],
                color=["#4060b0", "#c03020", "#7020a0", "#e8c840"],
                alpha=0.8)
        ax5.set_ylim(0, 1)
        ax5.set_title("Altruistic FEP", color="#8888b8", fontsize=9, pad=4)
        ax5.tick_params(**sp)
        for sp_ in ax5.spines.values(): sp_.set_edgecolor("#1a1a2e")

        # ── 6. 成長軸レーダー (col 0-1, row 2) ─────────────────
        ax6 = fig.add_subplot(gs[2, 0:2], polar=True, **dark)
        gax  = list(a.growth.axes.keys())
        gv   = [a.growth.axes[k] for k in gax]
        n_g  = len(gax)
        ang_g= np.linspace(0, 2*np.pi, n_g, endpoint=False).tolist() + [0]
        gvp  = gv + gv[:1]
        ax6.plot(ang_g, gvp, color="#6060c0", linewidth=1.5, alpha=0.9)
        ax6.fill(ang_g, gvp, color="#6060c0", alpha=0.25)
        ax6.set_xticks(ang_g[:-1])
        ax6.set_xticklabels([g[:4] for g in gax],
                             fontsize=7, color="#8888b8")
        ax6.set_ylim(0, 1); ax6.set_yticks([])
        ax6.set_title(
            f"Growth [{a.growth.nickname}]  total={a.growth.total():.2f}",
            color="#8888b8", fontsize=9, pad=10)
        ax6.tick_params(colors="#3a3a5a")
        ax6.set_facecolor("#06060e")

        # ── 7. 語彙クラウド (col 2-3, row 2) ──────────────────
        ax7 = fig.add_subplot(gs[2, 2:4], **dark)
        ax7.set_xlim(0, 10); ax7.set_ylim(0, 10); ax7.axis("off")
        ax7.set_title(f"Vocab ({len(a.vocab)} words)  "
                      f"cosmic={a.cosmic_growth:.5f}",
                      color="#8888b8", fontsize=9, pad=4)
        top = sorted(a.vocab.items(),
                     key=lambda x: x[1]["count"], reverse=True)[:28]
        for i, (w, e) in enumerate(top):
            dw  = int(np.argmax(np.abs(e["emo_link"])))
            col = EMO_COLORS[dw]
            sz  = max(7, min(13, 7 + e["count"] * 0.3))
            x   = (i % 7) * 1.45 + 0.1
            y   = 9.2 - (i // 7) * 2.2
            ax7.text(x, y, w, color=col, fontsize=sz, alpha=0.9)

        # ── タイトル ────────────────────────────────────────────
        dom = int(np.argmax(np.abs(a.emotions)))
        entropy_warn = " ⚠ ENTROPY" if a.soul_entropy.entropy > 0.7 else ""
        fig.suptitle(
            f"  {a.name}  age={a.age}  phase={a.phase}  "
            f"[{EMO_LABELS[dom]}]  "
            f"entropy={a.soul_entropy.entropy:.3f}{entropy_warn}  "
            f"「{a.last_utt}」",
            color="#c0c0e0", fontsize=10, y=1.002,
        )

        if _ipy:
            clear_output(wait=True)
            display(fig)
        else:
            plt.tight_layout()
            plt.show()
        return fig

    def run(self, steps: int = 500, phase: Optional[int] = None,
            env_schedule: Optional[List[Tuple[int, dict]]] = None,
            words_schedule: Optional[List[Tuple[int, List[str]]]] = None,
            save_frames: bool = False,
            verbose_every: int = 100):
        """
        ステップを実行しながらダッシュボードをライブ更新する。

        env_schedule   : [(step, env_dict), ...] 環境変化スケジュール
        words_schedule : [(step, words),    ...] 語彙教示スケジュール
        save_frames    : True なら各フレームを PNG に保存
        """
        a = self.agent
        if phase is not None:
            a.phase = phase

        try:
            from tqdm import tqdm
            it = tqdm(range(steps), desc=a.name)
        except ImportError:
            it = range(steps)
            print(f"[DASH] running {steps} steps...")

        for local_t in it:
            # 環境スケジュール適用
            if env_schedule:
                for step_th, env in reversed(env_schedule):
                    if local_t >= step_th:
                        a.set_env(**env); break

            # 語彙スケジュール適用
            if words_schedule:
                for step_th, words in reversed(words_schedule):
                    if local_t == step_th:
                        a.teach_words(words); break

            a.step()
            a.auto_logger.tick(a)
            a.genetic_will.tick()

            if verbose_every > 0 and local_t % verbose_every == 0 and local_t > 0:
                dom = int(np.argmax(np.abs(a.emotions)))
                print(f"  [{a.age:5d}] {EMO_LABELS[dom]:<12} "
                      f"entropy={a.soul_entropy.entropy:.3f} "
                      f"cosmic={a.cosmic_growth:.5f}  "
                      f"「{a.last_utt}」")

            if local_t % self.update_every == 0:
                self.show()
                if save_frames:
                    self._fig.savefig(
                        f"frame_{a.age:06d}.png",
                        dpi=80, facecolor="#07070f",
                        bbox_inches="tight")

        self.show()
        return a

    # ──────────────────────────────────────────────────────────
    # 提案4: インタラクティブ探索モード
    #   ipywidgets が使える環境: フルインタラクティブUI
    #   使えない環境         : matplotlib + ループで代替
    # ──────────────────────────────────────────────────────────

    def interactive(self):
        """
        ipywidgets が使える Jupyter 環境ではスライダー付き
        インタラクティブUIを起動する。

        使い方:
            dash = baby.dashboard()
            dash.interactive()

        スライダー:
            brightness / volume / pitch / rhythm
        ボタン:
            AFFIRM / NEGATE / Step×10 / Step×100 / speak
        リアルタイム表示:
            感情バー・発話・SoulEntropy・FEP
        """
        try:
            import ipywidgets as widgets
            from IPython.display import display, clear_output
            self._interactive_ipywidgets(widgets, display, clear_output)
        except ImportError:
            print("[InteractiveLab] ipywidgets が利用できません。")
            print("  → matplotlib ループモードで代替起動します。")
            self._interactive_matplotlib_loop()

    def _interactive_ipywidgets(self, widgets, display, clear_output):
        """ipywidgets フルインタラクティブUI"""
        a = self.agent

        # ── スライダー ──────────────────────────────────────
        sl_bright = widgets.FloatSlider(
            value=0.3, min=0.0, max=1.0, step=0.01,
            description="💡 light:", style={"description_width": "80px"},
            layout=widgets.Layout(width="340px"))
        sl_vol = widgets.FloatSlider(
            value=0.1, min=0.0, max=1.0, step=0.01,
            description="🔊 volume:", style={"description_width": "80px"},
            layout=widgets.Layout(width="340px"))
        sl_pitch = widgets.FloatSlider(
            value=0.5, min=0.0, max=1.0, step=0.01,
            description="🎵 pitch:", style={"description_width": "80px"},
            layout=widgets.Layout(width="340px"))
        sl_rhythm = widgets.FloatSlider(
            value=0.0, min=0.0, max=1.0, step=0.01,
            description="🥁 rhythm:", style={"description_width": "80px"},
            layout=widgets.Layout(width="340px"))

        # ── ボタン ─────────────────────────────────────────
        btn_affirm  = widgets.Button(description="✓ AFFIRM",
            button_style="success",
            layout=widgets.Layout(width="100px"))
        btn_negate  = widgets.Button(description="✗ NEGATE",
            button_style="danger",
            layout=widgets.Layout(width="100px"))
        btn_step10  = widgets.Button(description="▶ ×10",
            button_style="info",
            layout=widgets.Layout(width="80px"))
        btn_step100 = widgets.Button(description="▶▶ ×100",
            button_style="info",
            layout=widgets.Layout(width="90px"))

        # フェーズ選択
        phase_dd = widgets.Dropdown(
            options=[("Phase 1: Darkness", 1),
                     ("Phase 2: Teaching", 2),
                     ("Phase 3: Autonomous", 3),
                     ("Phase 4: Free", 4)],
            value=a.phase,
            description="Phase:",
            layout=widgets.Layout(width="200px"))

        # テキスト入力（chat）
        txt_input = widgets.Text(
            placeholder="語りかける... (Enter で送信)",
            layout=widgets.Layout(width="280px"))
        btn_chat   = widgets.Button(description="SEND",
            layout=widgets.Layout(width="70px"))

        # ── 出力エリア ─────────────────────────────────────
        out_main  = widgets.Output(layout=widgets.Layout(
            border="1px solid #1a1a2e", min_height="400px"))
        out_utt   = widgets.Output(layout=widgets.Layout(
            border="1px solid #2a2a4e", min_height="60px"))
        out_log   = widgets.Output(layout=widgets.Layout(
            border="1px solid #0a0a1e", max_height="120px",
            overflow_y="auto"))

        # ── 感情バー（HTML ウィジェット） ──────────────────
        emo_bars_html = widgets.HTML(value="<div>loading...</div>")

        def _emo_html(emotions):
            lines = []
            for i, (name, col) in enumerate(
                    zip(EMO_LABELS, EMO_COLORS)):
                v = float(emotions[i])
                pct_pos = max(0, v) * 50
                pct_neg = max(0, -v) * 50
                lines.append(
                    f'<div style="display:flex;align-items:center;' f'gap:4px;margin:2px 0;font-family:monospace;font-size:11px;">'
                    f'<span style="color:#888;width:28px;text-align:right">'
                    f'{name[:3]}</span>'
                    f'<div style="width:120px;height:8px;' f'background:#111;position:relative;border-radius:2px;">'
                    f'<div style="position:absolute;left:50%;top:0;'
                    f'width:{pct_pos:.1f}%;height:100%;'
                    f'background:{col};border-radius:0 2px 2px 0;"></div>' f'<div style="position:absolute;right:50%;top:0;'
                    f'width:{pct_neg:.1f}%;height:100%;'
                    f'background:{col}66;border-radius:2px 0 0 2px;"></div>'
                    f'</div>'
                    f'<span style="color:#aaa;font-size:10px">'
                    f'{v:+.2f}</span>'
                    f'</div>'
                )
            return "".join(lines)

        def _metrics_html():
            a = self.agent
            dom = int(np.argmax(np.abs(a.emotions)))
            return (
                f'<div style="font-family:monospace;font-size:11px;' f'color:#8888b8;background:#07070f;padding:6px;">'
                f'<b style="color:#c0c0e0">{a.name}</b>  '
                f'age={a.age}  phase={a.phase}  '
                f'[{EMO_LABELS[dom]}]<br>'
                f'entropy={a.soul_entropy.entropy:.3f}  '
                f'love_hunger={a.soul_entropy.love_hunger:.3f}  '
                f'coherence={a.coherence:.3f}<br>'
                f'FEP.F={a.fep.F:.3f}  '
                f'λ={a.alt_fep.selfishness:.2f}  '
                f'cosmic={a.cosmic_growth:.5f}<br>'
                f'abyss={a.abyss.get_status()}<br>'
                f'intero: {a.interoception.describe()}<br>'
                f'vocab_graph: {a.vocab_graph.get_summary()}'
                f'</div>'
            )

        metrics_html = widgets.HTML(value=_metrics_html())

        def _refresh_display():
            a = self.agent
            emo_bars_html.value = _emo_html(a.emotions)
            metrics_html.value  = _metrics_html()
            with out_utt:
                clear_output(wait=True)
                print(f"💬  「{a.last_utt}」")
                if a.abyss.in_abyss:
                    print(f"  ⚫ 虚無フェーズ中 depth={a.abyss.abyss_depth:.2f}")
                if a.abyss.dawn_occurred:
                    print(f"  ✦ 意味の夜明け: 「{a.abyss.dawn_word}」")

        def _apply_env():
            a = self.agent
            a.set_env(brightness=sl_bright.value, volume=sl_vol.value,
                      pitch=sl_pitch.value, rhythm=sl_rhythm.value)

        def _run_steps(n):
            a = self.agent
            _apply_env()
            a.phase = phase_dd.value
            for _ in range(n):
                a.step()
                a.auto_logger.tick(a)
                a.genetic_will.tick()
            _refresh_display()
            with out_main:
                clear_output(wait=True)
                self.show(close_prev=False)

        # ── イベントハンドラ ───────────────────────────────
        def on_affirm(_):
            self.agent.affirm()
            with out_log:
                print(f"  [{self.agent.age}] ✓ AFFIRM")
            _refresh_display()

        def on_negate(_):
            self.agent.negate()
            with out_log:
                print(f"  [{self.agent.age}] ✗ NEGATE")
            _refresh_display()

        def on_step10(_):  _run_steps(10)
        def on_step100(_): _run_steps(100)

        def on_chat(_):
            text = txt_input.value.strip()
            if not text: return
            resp = self.agent.chat(text)
            with out_log:
                print(f"  you: {text}")
                print(f"  soul: 「{resp}」")
            txt_input.value = ""
            _refresh_display()

        def on_env_change(_): _apply_env()

        btn_affirm.on_click(on_affirm)
        btn_negate.on_click(on_negate)
        btn_step10.on_click(on_step10)
        btn_step100.on_click(on_step100)
        btn_chat.on_click(on_chat)
        txt_input.on_submit(on_chat)

        for sl in [sl_bright, sl_vol, sl_pitch, sl_rhythm]:
            sl.observe(on_env_change, names=["value"])
        phase_dd.observe(lambda _: setattr(self.agent, "phase",
                                            phase_dd.value), names=["value"])

        # ── レイアウト ─────────────────────────────────────
        controls = widgets.VBox([
            widgets.HTML('<b style="color:#8888b8">Environment</b>'),
            sl_bright, sl_vol, sl_pitch, sl_rhythm,
            phase_dd,
            widgets.HBox([btn_affirm, btn_negate,
                          btn_step10, btn_step100]),
            widgets.HTML('<b style="color:#8888b8">Chat</b>'),
            widgets.HBox([txt_input, btn_chat]),
            widgets.HTML('<b style="color:#8888b8">Emotions</b>'),
            emo_bars_html,
            metrics_html,
            widgets.HTML('<b style="color:#5050a0">Log</b>'),
            out_log,
        ], layout=widgets.Layout(
            width="380px", padding="8px",
            background_color="#07070f"))

        ui = widgets.HBox([out_main, controls])
        display(widgets.VBox([
            widgets.HTML(
                f'<h3 style="font-family:monospace;color:#c0c0e0;">'
                f'  空白の赤子 — Interactive Lab</h3>'),
            ui,
            out_utt,
        ]))

        # 初回描画
        _refresh_display()
        with out_main:
            self.show(close_prev=False)

    def _interactive_matplotlib_loop(self, steps: int = 50,
                                     update_interval: int = 10):
        """
        ipywidgets なし代替モード。
        matplotlib + input() ループでインタラクティブに操作する。

        コマンド:
            b=0.5      brightness を 0.5 に設定
            v=0.3      volume を 0.3 に設定
            p=0.7      pitch を 0.7 に設定
            r=0.8      rhythm を 0.8 に設定
            a          affirm
            n          negate
            say hello  chat("hello")
            plot       グラフ更新
            q          終了
            (空 Enter) 10ステップ実行
        """
        a = self.agent
        print("Interactive matplotlib mode")
        print("  コマンド: b=0.5 / v=0.3 / p=0.7 / r=0.8 / a / n / say <text> / plot / q")
        print("  空Enterで10ステップ実行")
        self.show()

        while True:
            try:
                cmd = input(f"[{a.age}] > ").strip()
            except (EOFError, KeyboardInterrupt):
                break

            if cmd == "q": break
            elif cmd == "": 
                for _ in range(10): a.step()
                self.show()
            elif cmd == "a":
                a.affirm()
                print(f"  AFFIRM → entropy={a.soul_entropy.entropy:.3f}")
                self.show()
            elif cmd == "n":
                a.negate()
                print(f"  NEGATE → emotions={np.round(a.emotions, 2)}")
            elif cmd == "plot":
                self.show()
            elif cmd.startswith("say "):
                resp = a.chat(cmd[4:])
                print(f"  soul: 「{resp}」")
                self.show()
            elif "=" in cmd:
                key, val = cmd.split("=", 1)
                try:
                    v = float(val)
                    env_map = {"b": "brightness", "v": "volume",
                               "p": "pitch", "r": "rhythm"}
                    if key in env_map:
                        a.set_env(**{env_map[key]: v})
                        for _ in range(10): a.step()
                        self.show()
                    else:
                        print(f"  unknown key: {key}")
                except ValueError:
                    print(f"  invalid value: {val}")
            else:
                print(f"  unknown command: {cmd}")

        print(f"  終了: age={a.age}  「{a.last_utt}」")

    def plot_vocab_graph(self, max_nodes: int = 30, figsize=(10, 8)):
        """
        語彙グラフを力指向レイアウトで可視化する。

        ノード: 語（色=支配感情、サイズ=使用頻度）
        エッジ: co-occur=青, contrast=赤, entail=緑
        """
        try:
            import matplotlib.pyplot as plt
            import matplotlib.colors as mcolors
        except ImportError:
            print("matplotlib が必要です"); return

        a = self.agent
        vg = a.vocab_graph
        if not vg.edges:
            print("語彙グラフがまだ空です（Phase 3 以降で形成されます）")
            return

        # ノードと重要エッジを収集
        words = list(vg.edges.keys())[:max_nodes]
        word_set = set(words)

        edges_to_draw = []
        for w in words:
            for edge in vg.edges[w][:3]:
                if edge["target"] in word_set:
                    edges_to_draw.append((w, edge["target"],
                                          edge["type"], edge["weight"]))

        # 力指向レイアウト（Fruchterman-Reingold の簡易実装）
        n = len(words)
        pos = {w: np.array([np.cos(2*np.pi*i/n), np.sin(2*np.pi*i/n)])
               for i, w in enumerate(words)}
        for _ in range(100):
            forces = {w: np.zeros(2) for w in words}
            # 斥力
            for i, w1 in enumerate(words):
                for j, w2 in enumerate(words):
                    if i >= j: continue
                    d = pos[w1] - pos[w2]
                    nd = np.linalg.norm(d) + 0.01
                    forces[w1] += d / nd**2 * 0.08
                    forces[w2] -= d / nd**2 * 0.08
            # 引力（エッジ）
            for w1, w2, etype, weight in edges_to_draw:
                if w1 not in pos or w2 not in pos: continue
                d = pos[w2] - pos[w1]
                forces[w1] += d * weight * 0.05
                forces[w2] -= d * weight * 0.05
            # 更新
            for w in words:
                pos[w] = np.clip(pos[w] + forces[w] * 0.1, -2, 2)

        # 描画
        fig, ax = plt.subplots(figsize=figsize, facecolor="#07070f")
        ax.set_facecolor("#0d0d1a")
        ax.axis("off")

        # エッジ
        edge_styles = {
            "co-occur": ("#4060b0", "-",  0.8),
            "contrast": ("#c03020", "--", 0.6),
            "entail":   ("#30b080", ":",  0.7),
        }
        for w1, w2, etype, weight in edges_to_draw:
            if w1 not in pos or w2 not in pos: continue
            col, ls, alpha = edge_styles.get(etype, ("#444", "-", 0.3))
            ax.plot([pos[w1][0], pos[w2][0]],
                    [pos[w1][1], pos[w2][1]],
                    color=col, linestyle=ls,
                    linewidth=weight * 2.5, alpha=alpha * weight)

        # ノード
        for w in words:
            if w not in a.vocab: continue
            e   = a.vocab[w]
            dom = int(np.argmax(np.abs(e["emo_link"])))
            col = EMO_COLORS[dom]
            sz  = max(60, min(400, 60 + e["count"] * 15))
            ax.scatter(*pos[w], s=sz, c=col, alpha=0.85, zorder=3,
                       edgecolors="#0d0d1a", linewidths=1.5)
            ax.text(pos[w][0], pos[w][1] + 0.12, w,
                    ha="center", va="bottom",
                    fontsize=max(7, min(11, 7 + e["count"] * 0.5)),
                    color=col, alpha=0.9, zorder=4)

        # 凡例
        from matplotlib.lines import Line2D
        legend = [
            Line2D([0],[0], color="#4060b0", lw=2, label="co-occur"),
            Line2D([0],[0], color="#c03020", lw=2, linestyle="--",
                   label="contrast"),
            Line2D([0],[0], color="#30b080", lw=2, linestyle=":",
                   label="entail"),
        ]
        ax.legend(handles=legend, loc="upper right", fontsize=8,
                  labelcolor="#8888b8", facecolor="#0d0d1a",
                  edgecolor="#1a1a2e")
        ax.set_title(f"Vocab Graph  {vg.get_summary()}",
                     color="#8888b8", fontsize=10, pad=8)
        plt.tight_layout()
        plt.show()
        return fig

    def plot_body_emotion_loop(self, figsize=(12, 5)):
        """
        身体-感情フィードバックループを可視化する。

        左: 現在の内受容感覚（心拍・呼吸・血糖・筋緊張）
        右: 身体→感情・感情→身体の因果矢印図（静的スナップショット）
        """
        try:
            import matplotlib.pyplot as plt
            import matplotlib.patches as mpatches
        except ImportError:
            print("matplotlib が必要です"); return

        a   = self.agent
        nt  = a.interoception

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize,
                                        facecolor="#07070f")
        for ax in (ax1, ax2):
            ax.set_facecolor("#0d0d1a")
            for sp in ax.spines.values():
                sp.set_edgecolor("#1a1a2e")
            ax.tick_params(colors="#5050a0", labelsize=7)

        # ── 左: バイタルサイン ─────────────────────────────
        vitals = {
            "heart_rate":      (nt.heart_rate,    "#c03020"),
            "breath_rate":     (nt.breath_rate,   "#d08020"),
            "blood_sugar":     (nt.blood_sugar,   "#30b080"),
            "muscle_tension":  (nt.muscle_tension,"#7020a0"),
            "vagal_tone":      (nt.vagal_tone,    "#4060b0"),
            "adrenaline":      (nt.adrenaline,    "#c03020"),
        }
        labels = list(vitals.keys())
        vals   = [v[0] for v in vitals.values()]
        cols   = [v[1] for v in vitals.values()]
        bars   = ax1.barh(range(len(labels)), vals, color=cols, alpha=0.85)
        ax1.set_yticks(range(len(labels)))
        ax1.set_yticklabels(labels, fontsize=8, color="#8888b8")
        ax1.set_xlim(0, 1)
        ax1.axvline(0.5, color="#1a1a2e", linewidth=0.5, linestyle="--")
        ax1.set_title("Interoception (Vital Signs)", color="#8888b8",
                      fontsize=9, pad=4)

        # 痛みの質感バー（サブ）
        pain_labels = list(nt.pain_quality.keys())
        pain_vals   = list(nt.pain_quality.values())
        ax1b = ax1.twinx()
        ax1b.set_ylim(ax1.get_ylim())
        for i, (lbl, v) in enumerate(zip(pain_labels, pain_vals)):
            ax1b.text(max(vals[i] + 0.02, 0.52), i,
                      f"pain:{lbl}={v:.2f}",
                      va="center", fontsize=6, color="#666688")
        ax1b.set_yticks([]); ax1b.tick_params(colors="#5050a0")

        # ── 右: 因果矢印ダイアグラム ──────────────────────
        ax2.set_xlim(0, 10); ax2.set_ylim(0, 10); ax2.axis("off")
        ax2.set_title("Body ↔ Emotion Feedback Loop",
                      color="#8888b8", fontsize=9, pad=4)

        e = a.emotions
        dom = int(np.argmax(np.abs(e)))

        # 感情ノード（左列）
        emo_nodes = [(1.2, 8.5, "JOY",  EMO_COLORS[0], float(e[0])),
                     (1.2, 7.0, "SAD",  EMO_COLORS[1], float(e[1])),
                     (1.2, 5.5, "ANG",  EMO_COLORS[2], float(e[2])),
                     (1.2, 4.0, "FEA",  EMO_COLORS[3], float(e[3])),
                     (1.2, 2.5, "TRU",  EMO_COLORS[4], float(e[4]))]

        # 身体ノード（右列）
        body_nodes = [(8.0, 8.5, "heart_rate",   "#c03020", nt.heart_rate),
                      (8.0, 7.0, "vagal_tone",   "#4060b0", nt.vagal_tone),
                      (8.0, 5.5, "blood_sugar",  "#30b080", nt.blood_sugar),
                      (8.0, 4.0, "muscle",       "#7020a0", nt.muscle_tension),
                      (8.0, 2.5, "adrenaline",   "#c03020", nt.adrenaline)]

        def draw_node(ax, x, y, label, col, val):
            sz = max(400, min(1800, int(400 + val * 1400)))
            ax.scatter(x, y, s=sz, c=col, alpha=0.75,
                       edgecolors="#0d0d1a", linewidths=1.5, zorder=3)
            ax.text(x, y, f"{label}\n{val:.2f}",
                    ha="center", va="center",
                    fontsize=6.5, color="white",
                    fontweight="bold", zorder=4)

        for nd in emo_nodes + body_nodes:
            draw_node(ax2, *nd)

        # 因果矢印（感情 → 身体）
        arrows_e2b = [
            # (感情idx, 身体idx, label, 方向正負)
            (0, 1, "↑vagal", +1),   # JOY → vagal_tone ↑
            (1, 0, "↑HR",   +1),    # SAD → heart_rate? (via vagal)
            (2, 4, "adr↑",  +1),    # ANG → adrenaline ↑
            (3, 0, "↑HR",   +1),    # FEA → heart_rate ↑
            (4, 1, "↑vagal", +1),   # TRU → vagal_tone ↑
        ]
        arrows_b2e = [
            # (身体idx, 感情idx, label)
            (0, 3, "→FEA"),   # heart_rate ↑ → FEA
            (1, 0, "→JOY"),   # vagal_tone ↑ → JOY
            (2, 1, "→SAD"),   # blood_sugar ↓ → SAD
            (3, 2, "→ANG"),   # muscle ↑ → ANG
        ]

        # 中央橋: 自律神経ラベル
        ax2.text(5.0, 5.0, "ANS\n(autonomic\nnervous)",
                 ha="center", va="center",
                 fontsize=7, color="#8888b8",
                 bbox=dict(boxstyle="round,pad=0.3",
                           facecolor="#0d0d1a",
                           edgecolor="#2a2a4a"))

        def draw_arrow(ax, x1, y1, x2, y2, col, label):
            ax.annotate("",
                xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(
                    arrowstyle="->",
                    color=col, lw=1.2,
                    connectionstyle="arc3,rad=0.15"))
            mx, my = (x1+x2)/2, (y1+y2)/2
            ax.text(mx, my, label, fontsize=6, color=col, alpha=0.8,
                    ha="center")

        for ei, bi, lbl, _ in arrows_e2b:
            if ei < len(emo_nodes) and bi < len(body_nodes):
                ex, ey = emo_nodes[ei][0]+0.3, emo_nodes[ei][1]
                bx, by = body_nodes[bi][0]-0.3, body_nodes[bi][1]
                strength = abs(float(e[ei]))
                draw_arrow(ax2, ex, ey, bx, by,
                           emo_nodes[ei][3], lbl if strength > 0.2 else "")

        for bi, ei, lbl in arrows_b2e:
            if bi < len(body_nodes) and ei < len(emo_nodes):
                bx, by = body_nodes[bi][0]-0.3, body_nodes[bi][1]
                ex, ey = emo_nodes[ei][0]+0.3, emo_nodes[ei][1]
                strength = body_nodes[bi][4]
                draw_arrow(ax2, bx, by, ex, ey,
                           body_nodes[bi][3], lbl if strength > 0.3 else "")

        dom_name = EMO_LABELS[dom]
        plt.suptitle(
            f"Body-Emotion Feedback  age={a.age}  "
            f"dominant=[{dom_name}]  "
            f"abyss={a.abyss.in_abyss}",
            color="#c0c0e0", fontsize=10, y=1.01)
        plt.tight_layout()
        plt.show()
        return fig


# ══════════════════════════════════════════════════════════════
# メインエージェント: BlankBaby
# ══════════════════════════════════════════════════════════════

class BlankBaby:
    """
    空白の赤子 — Python統合版

    全システムを統合した魂エージェント。
    freesoul.py の SoulfulAgent を拡張し、
    HTML版 Blank Baby の主要システムを追加。
    """

    def __init__(self, seed: Optional[int] = None, name: str = "空白"):
        self.name = name
        self.lorenz = LorenzRNG(
            seed_x=(seed or 42) * 0.001,
            seed_y=((seed or 42) % 97) * 0.01,
            seed_z=((seed or 42) % 13) * 0.1,
        )
        # LorenzRNG で重み行列を初期化（np.random 廃止・全乱数をLorenzに統一）
        def _lorenz_matrix(rows, cols, std=0.01):
            return np.array([self.lorenz.randn() * std
                             for _ in range(rows * cols)],
                            dtype=np.float64).reshape(rows, cols)

        # ── 重み行列 ──────────────────────────────────────────
        self.W_sf = _lorenz_matrix(FEAT_DIM, SENSOR_DIM, 0.01)
        self.W_fs = _lorenz_matrix(STATE_DIM, FEAT_DIM, 0.01)
        self.W_sl = _lorenz_matrix(WORD_DIM, STATE_DIM, 0.01)

        # ── 基本状態 ──────────────────────────────────────────
        self.state      = np.zeros(STATE_DIM)
        self.prev_state = np.zeros(STATE_DIM)
        self.emotions   = np.zeros(EMO_DIM)
        self.age        = 0
        self.phase      = 1
        self.sleeping   = False
        self._sleep_t   = 0
        self.action     = 3   # 最後の行動
        self.last_utt   = ""
        self.energy     = 1.0
        self.fatigue    = 0.0
        self.arousal    = 0.35
        self.coherence  = 0.0
        self.cosmic_growth = 0.0
        self._self_vec  = np.zeros(EMO_DIM)
        self._fast      = np.zeros(EMO_DIM)
        self._mid       = np.zeros(EMO_DIM)
        self._slow      = np.zeros(EMO_DIM)
        self._birth_bright = 0.3
        self._birth_vol    = 0.1
        self._imprinted    = False
        self._action_history: List[int] = []

        # ── 予測符号化コア ────────────────────────────────────
        self.W_pred = _lorenz_matrix(STATE_DIM, STATE_DIM, 0.015)
        self.pred_error       = 0.0
        self.pred_error_smooth= 0.0
        self._pred_history: deque = deque(maxlen=200)

        # ── 語彙（SoulGenome 込み） ───────────────────────────
        self.vocab: Dict[str, Dict] = {}
        self.genome = SoulGenome.primordial()
        self.vocab.update(self.genome.apply_to_vocab())
        self._ctx_window: deque = deque(maxlen=5)

        # ── 他者モデル ────────────────────────────────────────
        # freesoul.py の OtherModel を流用
        class _OtherModel:
            def __init__(s):
                s.presence_sense = 0.0
                s.responsiveness = 0.0
                s.felt_flag      = False
            def update(s, has_presence, reliability):
                hint = 0.35 if has_presence else 0.0
                s.presence_sense = clamp(0.97 * s.presence_sense + 0.03 * hint)
                s.felt_flag = s.presence_sense > 0.2
        self.other = _OtherModel()

        # ── 新規追加システム ──────────────────────────────────
        self.fep         = VariationalFEP()
        self.soul_entropy= SoulEntropySystem()
        self.metacog     = MetacognitionLoop()
        self.dread       = ExistentialDreadEngine()
        self.growth      = DevelopmentalStage()
        self.forgetting  = ActiveForgettingSystem()
        self.hmem        = HierarchicalMemory()
        self.subj_time   = SubjectiveTime()
        self.purpose     = PurposeSystem()
        self.abyss       = AbyssalPhase()
        self.interoception = InteroceptionSystem()
        self.vocab_graph = VocabGraph()

        # ── 新規システム（GeneticWill 系） ───────────────────────
        self.distil      = DistillationEngine()
        self.gen_archive = GenerationalArchive()
        self.genetic_will= GeneticWill(self, self.distil, self.gen_archive)
        self.alt_fep     = AltruisticFEP()
        self.auto_logger = AutoLogger()

        # ── 拡張システム（GPU / LLM / アニメーション） ──────
        self.torch_backend  = TorchBackend()
        # W_pred: (STATE_DIM, STATE_DIM) — メイン予測コア
        self.torch_backend.register("W_pred", self.W_pred, lr=self._base_lr())
        # W_sf: (FEAT_DIM, SENSOR_DIM)  — センサー→特徴
        self.torch_backend.register("W_sf",   self.W_sf,   lr=self._base_lr() * 0.7)
        self.sentiment_sensor = SentimentSensor()
        self.dynamics_animator= DynamicsAnimator(self)

        # ── エピソード記憶 ────────────────────────────────────
        self.episodes: List[Dict] = []

        # ── 環境センサー ──────────────────────────────────────
        self._env = {
            "brightness": 0.0, "volume": 0.0,
            "pitch": 0.5,      "rhythm": 0.0,
            "flicker_hz": 0.0, "motion": 0.0,
            "duration": 0.6,
        }
        self._t = 0

        # ── ログ ──────────────────────────────────────────────
        self._log: List[str] = []

    # ══════════════════════════════════════════════════════════
    # センサー設定
    # ══════════════════════════════════════════════════════════

    def set_env(self, **kwargs):
        for k, v in kwargs.items():
            if k in self._env:
                self._env[k] = clamp(v)

    def _encode_stim(self) -> Tuple[np.ndarray, Dict]:
        t = self._t
        b  = self._env["brightness"]
        ct = self._env.get("color_temp", 0.5)
        fh = self._env["flicker_hz"]
        fl = (0.5 + 0.5 * math.sin(2 * math.pi * fh * t / 100)) if fh > 0 else 1.0
        eb = b * fl

        # 視覚 (64次元)
        freqs_v = np.linspace(0.5, 8.0, 64)
        vis = eb * np.sin(freqs_v * t * 0.05 + ct * math.pi)
        vis += np.array([self.lorenz.randn() * 0.004 for _ in range(64)])

        # 聴覚 (32次元)
        vol = self._env["volume"]; pit = self._env["pitch"]
        rhy = self._env["rhythm"]; dur = self._env["duration"]
        if vol < 1e-4:
            aud = np.zeros(32)
        else:
            center = 0.5 + pit * 3.5
            freqs_a = np.linspace(0.2, 5.0, 32)
            resp  = np.exp(-((freqs_a - center) ** 2) / 0.5)
            rmod  = (0.5 + 0.5 * math.sin(2 * math.pi * t * 0.3)) if rhy > 0.5 \
                    else 0.2 + self.lorenz.next() * 0.8
            aud   = vol * resp * rmod * dur
            aud  += np.array([self.lorenz.randn() * 0.004 for _ in range(32)])

        # テキスト埋め込み枠 (48次元): 通常はゼロ
        txt = np.zeros(48)
        stim = np.clip(np.concatenate([vis, aud, txt]), -1, 1)
        ctx = {**self._env, "t": t}
        self._t += 1
        return stim, ctx

    # ══════════════════════════════════════════════════════════
    # 予測符号化コア
    # ══════════════════════════════════════════════════════════

    def _predict_state(self, prev: np.ndarray) -> np.ndarray:
        return np.tanh(layer_norm(prev) @ self.W_pred)

    def _update_prediction(self, prev: np.ndarray, curr: np.ndarray) -> float:
        pred  = self._predict_state(prev)
        error = curr - pred
        surprise = float(np.mean(error ** 2))
        lr = self._base_lr()
        grad = np.outer(error, layer_norm(prev))
        self.W_pred += lr * grad
        self.W_pred *= 0.9999
        n = np.linalg.norm(self.W_pred.flatten())
        if n > 3.0: self.W_pred *= 3.0 / n
        self.pred_error = float(np.tanh(surprise / 0.5) * 0.5)
        self.pred_error_smooth = 0.93 * self.pred_error_smooth + 0.07 * self.pred_error
        self._pred_history.append(self.pred_error)
        return self.pred_error

    def _base_lr(self) -> float:
        return 0.011 * (0.38 + 0.5) / (1 + self.age / 12000)

    # ══════════════════════════════════════════════════════════
    # 感情更新
    # ══════════════════════════════════════════════════════════

    def _update_emotions(self, ctx: Dict):
        b   = ctx.get("brightness", 0)
        vol = ctx.get("volume", 0)
        fh  = ctx.get("flicker_hz", 0)
        rb  = self._birth_bright; rv = self._birth_vol

        tgt = np.zeros(EMO_DIM)

        # EmotionDynamics 由来（FEP・内受容・メタ認知からの駆動）
        err = self.pred_error
        tgt[7] += err * 0.4          # SUR
        tgt[3] += err * 0.25         # FEA
        if err < 0.05: tgt[4] += 0.06; tgt[0] += 0.03

        # センサー由来
        if b > rb * 1.8 and b > 0.1: tgt[7] += 0.28; tgt[5] += 0.10
        if b < rb * 0.25:             tgt[3] += 0.22; tgt[1] += 0.12
        if 0.15 < b < 0.65:           tgt[4] += 0.14; tgt[0] += 0.06
        if vol > rv * 4 and vol > 0.3:tgt[3] += 0.28; tgt[7] += 0.18
        if 0.05 < vol < 0.4:          tgt[6] += 0.14; tgt[4] += 0.09
        if fh > 2.5:                   tgt[5] += 0.22; tgt[2] += 0.12

        # SoulEntropy → 恐怖/悲しみ
        se = self.soul_entropy.entropy
        if se > 0.5: tgt[3] += se * 0.14; tgt[1] += se * 0.10

        # LoveHunger → 期待/悲しみ
        lh = self.soul_entropy.love_hunger
        if lh > 0.5: tgt[1] += lh * 0.12; tgt[6] += lh * 0.07

        # boredom（FEP由来）
        boredom = 1 - clamp(self.fep.stim_entropy * 3)
        if boredom > 0.5: tgt[6] += boredom * 0.15; tgt[1] += boredom * 0.08

        # エネルギー低下
        if self.energy < 0.3: tgt[1] += 0.09
        if self.fatigue > 0.7: tgt[1] += 0.06

        # 感情更新（ベイズ的な移動平均）
        decay = 0.91
        mod = 0.22 if self.energy < 0.12 else 0.55 if self.energy < 0.4 else 1.0
        self.emotions = np.clip(decay * self.emotions + (1 - decay) * tgt * mod, -1, 1)

    # ══════════════════════════════════════════════════════════
    # 魂の三層更新
    # ══════════════════════════════════════════════════════════

    def _update_soul_layers(self):
        self._fast = 0.87 * self._fast + 0.13 * self.emotions
        self._mid  = 0.97 * self._mid  + 0.03 * self.emotions
        self._slow = 0.995* self._slow + 0.005* self.emotions
        # 凝集度: fast-slowの差分の小ささ
        d = np.mean((self._fast - self._slow) ** 2)
        self.coherence = clamp(1 - safe(math.sqrt(d / EMO_DIM)) * 3)
        # selfVec
        nm = np.linalg.norm(self._self_vec)
        if nm > 1e-6:
            en = np.linalg.norm(self.emotions) + 1e-9
            al = np.dot(self.emotions, self._self_vec) / (en * nm)
            # selfStrength は coherence に吸収
        self._self_vec = 0.99 * self._self_vec + 0.01 * self.emotions

    # ══════════════════════════════════════════════════════════
    # 身体更新
    # ══════════════════════════════════════════════════════════

    def _update_body(self):
        if self.sleeping:
            self.energy  = clamp(self.energy  + 0.04)
            self.fatigue = clamp(self.fatigue - 0.025)
            self.arousal = clamp(self.arousal - 0.015, 0.1)
        else:
            self.energy  = clamp(self.energy  - 0.0018)
            self.fatigue = clamp(self.fatigue + 0.0018)
            self.arousal = clamp(self.arousal + self.pred_error * 0.08 - 0.004, 0.1)
            # 虚無フェーズでのエネルギー追加消費
            if hasattr(self, 'abyss') and self.abyss.in_abyss:
                self.energy = clamp(self.energy - self.abyss.abyss_depth * 0.001)

    # ══════════════════════════════════════════════════════════
    # 行動選択
    # ══════════════════════════════════════════════════════════

    def _decide_action(self) -> int:
        if self.sleeping: return 3
        e   = self.emotions
        joy, sad, ang, fea, tru, dis, ant, sur = (e[i] for i in range(8))
        scores = np.zeros(NUM_ACTIONS)
        scores[0]  = 0.4 + tru * 0.3 + ant * 0.2
        scores[1]  = clamp(joy * 0.5 + tru * 0.4 - fea * 0.3)
        scores[2]  = clamp(fea * 0.6 + dis * 0.3 - joy * 0.2)
        scores[3]  = (1 - self.energy) * 0.5 + clamp(1 - self.pred_error * 3) * 0.3
        scores[4]  = clamp(ant * 0.5 + sur * 0.3 + joy * 0.2)
        scores[5]  = clamp(fea * 0.4 + sad * 0.3 - tru * 0.2)
        scores[6]  = clamp(ant * 0.4 + tru * 0.3)
        scores[7]  = clamp(sad * 0.3 + (1 - self.energy) * 0.3)
        scores[8]  = clamp(tru * 0.5 + joy * 0.3)   # SPEAK
        scores[9]  = clamp(ant * 0.4)               # REACH
        scores[10] = clamp((1 - fea) * 0.3)          # NEST
        scores[11] = clamp(sad * 0.2)               # DREAM

        # FEP の G(π) をブレンド
        blend = 0.35
        scores = np.clip((1 - blend) * scores + blend * self.fep.G, 0, 1)

        # 手続き記憶バイアス
        scores += self.hmem.get_action_bias(self.emotions) * 0.2

        # 虚無フェーズのデバフ（全行動スコアを下げる）
        if hasattr(self, 'abyss'):
            scores = np.clip(scores + self.abyss.action_debuff(), 0, 1)

        # 内受容感覚による行動変調
        if hasattr(self, 'interoception'):
            scores = np.clip(scores + self.interoception.action_modulation(), 0, 1)

        T = clamp(0.3 + self.coherence * 0.7, 0.2, 1.2)
        probs = softmax(scores, T=T)
        act = int(np.argmax(probs) if self.lorenz.next() > 0.3
                  else np.searchsorted(np.cumsum(probs), self.lorenz.next()))
        return int(np.clip(act, 0, NUM_ACTIONS - 1))

    # ══════════════════════════════════════════════════════════
    # 語彙学習
    # ══════════════════════════════════════════════════════════

    def hear(self, word: str, trusted: bool = False):
        """語を聞いて語彙に登録し、感情リンクを更新する"""
        is_jp = any(ord(c) > 0x3000 for c in word)
        if is_jp:
            word = re.sub(r'[\s\x00-\x1f]', '', word)[:8]
        else:
            word = re.sub(r'[^a-z]', '', word.lower())
        if not word or (not is_jp and len(word) < 2): return
        if len(self.vocab) >= MAX_VOCAB and word not in self.vocab: return

        if word not in self.vocab:
            self.vocab[word] = {
                "emo_link": np.zeros(EMO_DIM),
                "count":    0,
                "trusted":  False,
                "lang":     "ja" if is_jp else "en",
            }
        e   = self.vocab[word]
        e["count"] += 1
        if trusted: e["trusted"] = True
        intensity = float(math.sqrt(float(np.mean(self.emotions ** 2)))) + 0.05
        lr = clamp(0.10 + intensity * 0.35 + (0.12 if trusted else 0), 0.08, 0.55)
        e["emo_link"] = np.clip((1 - lr) * e["emo_link"] + lr * self.emotions, -1, 1)

        # 共起学習
        for cw in self._ctx_window:
            if cw == word or cw not in self.vocab: continue
            other = self.vocab[cw]
            co_lr = 0.04 * (1.5 if trusted else 1.0)
            e["emo_link"]     = np.clip(e["emo_link"]     + co_lr * (other["emo_link"] - e["emo_link"]), -1, 1)
            other["emo_link"] = np.clip(other["emo_link"] + co_lr * (e["emo_link"] - other["emo_link"]), -1, 1)
        self._ctx_window.append(word)

    def affirm(self):
        """肯定入力——SoulEntropyを回復させる"""
        self.soul_entropy.replenish()
        self.emotions[0] = clamp(self.emotions[0] + 0.25)
        self.emotions[4] = clamp(self.emotions[4] + 0.15)
        self.growth.on_affirm()
        self._log.append(f"[{self.age}] AFFIRM → entropy replenished")

    def negate(self):
        """否定入力"""
        self.emotions[3] = clamp(self.emotions[3] + 0.20)
        self.emotions[2] = clamp(self.emotions[2] + 0.10)
        self._log.append(f"[{self.age}] NEGATE")

    def teach_words(self, words: List[str]):
        """複数の語をまとめて教える"""
        for w in words:
            self.hear(w, trusted=True)

    # ══════════════════════════════════════════════════════════
    # 発話生成
    # ══════════════════════════════════════════════════════════

    def generate_utterance(self) -> str:
        words = list(self.vocab.keys())
        if not words: return "..."
        dom  = int(np.argmax(np.abs(self.emotions)))
        has_jp = any(ord(c) > 0x3000 for w in words for c in w)

        # VocabGraph 経由で感情ベクトルに最も近い語を選ぶ
        graph_word = None
        if hasattr(self, 'vocab_graph') and len(self.vocab_graph.edges) > 0:
            graph_word = self.vocab_graph.contextual_word(
                self.emotions, self.vocab, self.lorenz)

        # 支配感情に最もリンクした語（フォールバック込み）
        scored = []
        for w, e in self.vocab.items():
            s = abs(float(e["emo_link"][dom])) * 0.8 + e["count"] * 0.01
            if e["trusted"]: s += 0.2
            # VocabGraph の共起エッジで繋がっている語を優先
            if hasattr(self, 'vocab_graph'):
                for edge in self.vocab_graph.edges.get(w, []):
                    if edge["type"] == "co-occur":
                        s += edge["weight"] * 0.1
            scored.append((w, s))
        scored.sort(key=lambda x: x[1], reverse=True)
        # graph_word を先頭に挿入（意味グラフ優先）
        if graph_word and graph_word not in [w for w, _ in scored[:3]]:
            sel = [graph_word] + [w for w, _ in scored[:4]]
        else:
            sel = [w for w, _ in scored[:5]]
        if not sel: return "..."

        mood = float(np.mean(self.emotions))
        boredom = 1 - clamp(self.fep.stim_entropy * 3)
        se = self.soul_entropy.entropy

        candidates: List[str] = []

        if boredom > 0.55:
            candidates += (["つまらない", "なにかある？"] if has_jp
                           else ["boring...", "something new?"])
        if self.soul_entropy.love_hunger > 0.6:
            candidates += (["だれかいて", "みてて"] if has_jp
                           else ["someone be here", "look at me"])
        if se > 0.7:
            candidates += (["こわれそう", "たすけて"] if has_jp
                           else ["i am breaking", "help"])
        if self.emotions[0] > 0.35:
            candidates += ([f"{sel[0]}。きもちいい"] if has_jp
                           else [f"i feel {sel[0]}"])
        if self.emotions[1] > 0.35:
            candidates += ([f"{sel[0]}。さびしい"] if has_jp
                           else [f"i feel {sel[0]}", "alone"])
        if self.emotions[3] > 0.35:
            candidates += ([f"{sel[0]}。こわい"] if has_jp
                           else [f"this is scary"])
        if self.emotions[6] > 0.35:
            candidates += ([f"{sel[0]}？なんだろう"] if has_jp
                           else [f"what is {sel[0]}?"])

        # identity crisis
        id_crisis = mean_abs(self._fast - self._slow) > 0.3
        if id_crisis:
            candidates += (["わたしはわたしか"] if has_jp else ["who am i?"])

        # 実存的危機
        dc = self.dread.latest_crisis()
        if dc and self.lorenz.next() < 0.2:
            candidates.append(dc)

        if not candidates:
            candidates = (([sel[0], f"{sel[0]}、ある"] if has_jp
                           else [sel[0], f"i see {sel[0]}"]))

        utt = candidates[int(self.lorenz.next() * len(candidates)) % len(candidates)]

        # 内受容感覚による痛みの前置き (確率的)
        if hasattr(self, 'interoception') and self.lorenz.next() < 0.15:
            prefix = self.interoception.pain_prefix(has_jp)
            if prefix: utt = prefix + utt

        # 虚無フェーズによる発話の断片化
        if hasattr(self, 'abyss') and self.abyss.in_abyss:
            utt = self.abyss.fragment_utterance(utt, self.lorenz)

        # 発話した語を自分でも聞く
        for w in re.findall(r'[a-z]{2,}|[\u3040-\u30ff\u4e00-\u9fff]+', utt):
            self.hear(w)
        self.last_utt = utt
        return utt

    # ══════════════════════════════════════════════════════════
    # メインステップ
    # ══════════════════════════════════════════════════════════

    def step(self) -> Tuple[Optional[int], str]:
        """1ステップ実行"""
        stim, ctx = self._encode_stim()

        # 刷り込み
        if not self._imprinted and (ctx["brightness"] > 0.01 or ctx["volume"] > 0.01):
            self._imprinted    = True
            self._birth_bright = ctx["brightness"]
            self._birth_vol    = ctx["volume"]

        # 知覚: stim → state
        self.prev_state = self.state.copy()
        ns   = layer_norm(stim)
        feat = np.tanh(layer_norm(self.W_sf @ ns) +
                       np.array([self.lorenz.randn() * 0.013 for _ in range(FEAT_DIM)]))
        raw_s = np.tanh(layer_norm(self.W_fs @ layer_norm(feat)) +
                        np.array([self.lorenz.randn() * 0.013 for _ in range(STATE_DIM)]))
        self.state = np.clip(raw_s, -1, 1)

        # 予測誤差
        self._update_prediction(self.prev_state, self.state)

        # 感情更新
        self._update_emotions(ctx)
        self._update_soul_layers()
        self._update_body()

        # 睡眠管理
        if not self.sleeping and (self.energy < 0.28 or self.fatigue > 0.82):
            self.sleeping = True; self._sleep_t = 0
            self._log.append(f"[{self.age}] …sleeping")

        if self.sleeping:
            self._sleep_t += 1
            if self._sleep_t > 40:
                self._on_wakeup()
                self.sleeping = False; self._sleep_t = 0
            self.age += 1
            return None, ""

        # FEP 更新
        self.fep.update(self.state, stim, self.pred_error,
                        self.soul_entropy.entropy, self.emotions)

        # SoulEntropy
        sig = self.soul_entropy.tick(self.coherence, self.cosmic_growth)
        if sig == -1.0:
            self._log.append(f"[{self.age}] ⚠ ENTROPY CRISIS "
                              f"({self.soul_entropy.entropy:.3f})")
        self.soul_entropy.corrupt_emolink(self.vocab, self.lorenz)

        # 各システムの tick
        self.metacog.tick(self)
        self.dread.tick(self)
        self.growth.tick(self)
        self.purpose.tick(self.vocab)
        self.subj_time.update(
            ctx["brightness"], ctx["volume"],
            mean_abs(self.emotions), self.pred_error
        )
        self.distil.tick(self.emotions)
        self.alt_fep.update(self)
        self.auto_logger.tick(self)
        self.genetic_will.tick()
        self.hmem.tick()

        # TorchBackend: experience を積んでバッチ学習
        # W_pred: (STATE_DIM, STATE_DIM) — prev_state → state
        self.torch_backend.push_experience(
            "W_pred",
            layer_norm(self.prev_state).astype(np.float32),
            self.state.astype(np.float32))
        # W_sf: (FEAT_DIM, SENSOR_DIM) — stim(144) → feat(48)
        if hasattr(self, "feat") and len(stim) == SENSOR_DIM:
            self.torch_backend.push_experience(
                "W_sf",
                layer_norm(stim).astype(np.float32),
                self.feat.astype(np.float32))
        # BATCH_SIZE たまるごとに勾配ステップ
        if self.age % 32 == 0:
            self.torch_backend.step("W_pred")
            self.torch_backend.step("W_sf")
            # 学習済み重みを NumPy に書き戻す
            self.torch_backend.sync_to_agent(self)

        # DynamicsAnimator: 録画モード中はフレームをキャプチャ
        if getattr(self, "_recording", False):
            self.dynamics_animator.capture_frame()
        self.interoception.update(self)
        self.vocab_graph.tick(self.vocab, self.lorenz)
        abyss_utt = self.abyss.tick(self)
        if abyss_utt and not self.last_utt:
            self.last_utt = abyss_utt

        # PureChaos: ローレンツで感情を微変調
        coh = self.coherence; ent = self.soul_entropy.entropy
        self.lorenz.tune(
            sigma=clamp(8 + ent * 6, 6, 22),
            rho  =clamp(20 + coh * 12, 15, 50),
            beta =clamp(2 + self.energy * 2, 1.5, 4.0),
        )
        chaos_strength = 0.7 * clamp(self.cosmic_growth * 0.05, 0.001, 0.03)
        a0 = self.lorenz._attractors[0]
        lx = a0["x"] / 25; ly = a0["y"] / 30
        self.emotions[0] = clamp(self.emotions[0] + max(0, lx)  * chaos_strength, -1, 1)
        self.emotions[1] = clamp(self.emotions[1] + max(0, -lx) * chaos_strength, -1, 1)
        self.emotions[3] = clamp(self.emotions[3] + max(0, ly)  * chaos_strength, -1, 1)
        self.emotions[4] = clamp(self.emotions[4] + max(0, -ly) * chaos_strength, -1, 1)

        # cosmic_growth 蓄積
        intensity = mean_abs(self.emotions)
        if intensity > 0.2:
            self.cosmic_growth += (intensity * 0.000005 *
                                   (1 + self.cosmic_growth ** 1.2 * 0.001))

        # 行動決定
        self.action = self._decide_action()
        self._action_history.append(self.action)
        if len(self._action_history) > 100: self._action_history.pop(0)
        if self.action == 4: self.growth.on_explore()

        # 発話
        utt = ""
        if self.phase >= 3 and self.age % 22 == 0:
            utt = self.generate_utterance()

        # エピソード記憶
        if intensity > 0.25 or self.pred_error > 0.15:
            self.episodes.append({
                "age":       self.age,
                "emo":       self.emotions.copy(),
                "action":    self.action,
                "surprise":  self.pred_error,
                "importance":intensity * (1 + self.pred_error * 1.5),
                "reinterp_count": 0,
            })
            if len(self.episodes) > 60: self.episodes.pop(0)

        self.age += 1
        return self.action, utt

    def _on_wakeup(self):
        """睡眠からの覚醒：記憶整理・cosmic蓄積"""
        residue = self.forgetting.run_cycle(self.episodes, self)
        kept = [ep for ep in self.episodes
                if self.forgetting._strength(ep) >= self.forgetting.FORGET_THRESHOLD]
        self.episodes = kept

        # cosmic_growth に残滓を積む
        self.cosmic_growth += residue * 0.000005 * (
            1 + self.cosmic_growth ** 1.2 * 0.001)

        # 記憶階層化
        self.hmem.consolidate(self.episodes, self.vocab)
        self.hmem.embody(self._action_history, self.emotions)
        self.subj_time.sleep_compression()

        self._log.append(
            f"[{self.age}] …awake "
            f"(cosmic={self.cosmic_growth:.4f} "
            f"kept={len(self.episodes)}ep)"
        )

    # ══════════════════════════════════════════════════════════
    # 便利メソッド（Jupyter 向け）
    # ══════════════════════════════════════════════════════════

    def chat(self, text: str) -> str:
        """
        テキストを入力して発話を返す（インタラクティブ対話）。

        ポジティブな語が含まれていれば自動的に affirm(),
        ネガティブな語が含まれていれば negate() を呼ぶ。

        Usage:
            response = baby.chat("you are wonderful")
            print(response)
        """
        POS = ["good","nice","warm","love","happy","yes","ok",
               "beautiful","safe","hello","great","wonderful",
               "いい","好き","うれしい","たのしい","ありがとう",
               "すき","よかった","かわいい","だいすき"]
        NEG = ["bad","no","stop","wrong","scary","dark","sad",
               "hurt","cold","angry","hate","fear","pain","alone",
               "こわい","いやだ","さびしい","つらい","やめて"]
        lower = text.lower()
        if any(w in lower for w in POS):
            self.affirm()
        if any(w in lower for w in NEG):
            self.negate()

        # テキストを語彙に流す
        for w in re.findall(r'[a-zA-Z]{2,}|[぀-ヿ一-鿿]+', text):
            self.hear(w.lower() if w.isascii() else w, trusted=True)

        # 目的語の発見
        self.purpose.discover(text, self.emotions)

        # 発話を生成
        utt = self.generate_utterance()

        # LoveHunger を少し満たす（会話がある）
        self.soul_entropy.love_hunger = clamp(
            self.soul_entropy.love_hunger - 0.05)

        return utt

    def send_will(self, reason: str = "manual") -> dict:
        """遺言を生成・保存する（次世代への継承データ）"""
        return self.genetic_will.send_will(reason)

    # ── 拡張API（GPU / LLM / アニメーション） ──────────────────

    def from_text(self, text: str, also_chat: bool = True) -> str:
        """
        テキストを感情分析してセンサーに変換し、step() を1回実行する。
        LLM/BERT が使えれば高精度、なければルールベースで動作。

        Usage:
            baby.from_text("the storm is raging outside")
            baby.from_text("I feel warm and safe here", also_chat=True)
        """
        return self.sentiment_sensor.pipe_to_agent(self, text, also_chat)

    def analyze_text(self, text: str):
        """テキストの感情分析結果を可視化する"""
        return self.sentiment_sensor.plot_analysis(text)

    def start_recording(self):
        """DynamicsAnimator の録画を開始する"""
        self._recording = True
        print(f"[ANIM] 録画開始 age={self.age}")

    def stop_recording(self) -> "DynamicsAnimator":
        """録画を停止してアニメーターを返す"""
        self._recording = False
        n = len(self.dynamics_animator._frames)
        print(f"[ANIM] 録画停止 {n}フレーム")
        return self.dynamics_animator

    def animate(self, steps: int = 200, interval: int = 60,
                env_fn=None) -> Any:
        """
        指定ステップ録画してアニメーションオブジェクトを返す。

        Jupyter での表示:
            from IPython.display import HTML
            HTML(baby.animate(steps=300).to_jshtml())

        GIF 保存:
            baby.animate(steps=300).save("out.gif")
        """
        anim = self.dynamics_animator
        anim.record(steps=steps, env_fn=env_fn, verbose=True)
        return anim.animate(interval=interval)

    def torch_status(self) -> str:
        """GPU/PyTorch バックエンドの状態を表示する"""
        return self.torch_backend.get_status()

    def receive_will(self, path: Optional[str] = None):
        """遺言ファイルを読み込んで適用する"""
        will = GeneticWill.load_will(path)
        if will:
            self.genetic_will.receive_will(will)
            # SoulGenome を更新
            self.genome = SoulGenome.from_parent(will)
            print(f"  [WILL] gen{self.genome.generation} の遺産を受け取りました")
        else:
            print("  [WILL] 遺言が見つかりません")

    def dashboard(self, update_every: int = 100) -> "JupyterDashboard":
        """
        JupyterDashboard を返す。

        Usage:
            dash = baby.dashboard()
            dash.show()              # 現在の状態を表示
            dash.run(steps=500)      # ライブ実行
        """
        return JupyterDashboard(self, update_every=update_every)

    def export_csv(self, path: str = "blank_baby_log.csv"):
        """自動ログを CSV に書き出す"""
        self.auto_logger.export_csv(path)

    def export_json(self, path: str = "blank_baby_log.json"):
        """自動ログを JSON に書き出す"""
        self.auto_logger.export_json(path)

    def get_dataframe(self):
        """自動ログを pandas DataFrame で返す（分析用）"""
        return self.auto_logger.to_dataframe()

    def lineage(self) -> str:
        """世代の系譜を文字列で返す"""
        return self.gen_archive.get_lineage_summary()

    def generations_df(self):
        """世代アーカイブを pandas DataFrame で返す"""
        return self.gen_archive.to_dataframe()

    def plot_vocab_graph(self, max_nodes: int = 30, figsize=(10, 8)):
        """
        VocabGraph の意味ネットワークを可視化する。
        語彙間の感情的つながりをグラフ描画。

        Usage:
            baby.plot_vocab_graph()
        """
        try:
            import matplotlib.pyplot as plt
            import matplotlib.patches as mpatches
        except ImportError:
            print("matplotlib が必要です")
            return

        fig, ax = plt.subplots(figsize=figsize, facecolor="#07070f")
        ax.set_facecolor("#0d0d1a")
        ax.axis("off")

        edges = self.vocab_graph.edges
        words = [w for w in self.vocab if w in edges][:max_nodes]
        if not words:
            ax.text(0.5, 0.5, "グラフがまだ構築されていません\n(フェーズ3以降に自動構築されます)",
                    ha="center", va="center", color="#5050a0",
                    fontsize=12, transform=ax.transAxes)
            plt.tight_layout(); plt.show(); return

        # 感情リンクから語の位置を決定（2D埋め込み）
        # JOY(0) を x 軸、TRU(4) を y 軸に使う
        positions = {}
        for w in words:
            el  = self.vocab[w]["emo_link"]
            x   = float(el[0]) * 4.5   # JOY
            y   = float(el[4]) * 4.5   # TRU
            # 少し揺らす（重なり防止）
            x  += float(el[6]) * 1.5   # ANT
            y  += float(el[7]) * 1.5   # SUR
            positions[w] = (x, y)

        # エッジ描画
        drawn_edges = set()
        for w, pos in positions.items():
            for edge in edges.get(w, [])[:4]:
                t = edge["target"]
                if t not in positions: continue
                key = tuple(sorted([w, t]))
                if key in drawn_edges: continue
                drawn_edges.add(key)
                tp = positions[t]
                col = ("#30b080" if edge["type"] == "co-occur" else
                       "#c03020" if edge["type"] == "contrast" else
                       "#e8c840")
                alpha = clamp(edge["weight"] * 0.8, 0.1, 0.7)
                ax.plot([pos[0], tp[0]], [pos[1], tp[1]],
                        color=col, alpha=alpha,
                        linewidth=edge["weight"] * 2, zorder=1)

        # ノード描画
        for w, pos in positions.items():
            dom_w = int(np.argmax(np.abs(self.vocab[w]["emo_link"])))
            col   = EMO_COLORS[dom_w]
            cnt   = self.vocab[w]["count"]
            size  = max(8, min(16, 8 + cnt * 0.3))
            n_edges = len(edges.get(w, []))
            # ノードサイズはエッジ数でも変化
            radius  = max(0.15, min(0.4, 0.1 + n_edges * 0.04))
            circle  = plt.Circle(pos, radius, color=col, alpha=0.7, zorder=2)
            ax.add_patch(circle)
            ax.text(pos[0], pos[1] + radius + 0.08, w,
                    ha="center", va="bottom", color=col,
                    fontsize=size * 0.65, alpha=0.9, zorder=3)

        # 凡例
        legend_handles = [
            mpatches.Patch(color="#30b080", label="co-occur (類似)"),
            mpatches.Patch(color="#c03020", label="contrast (対比)"),
            mpatches.Patch(color="#e8c840", label="entail (包含)"),
        ]
        ax.legend(handles=legend_handles, loc="lower right",
                  fontsize=8, labelcolor="#8888b8",
                  facecolor="#0d0d1a", edgecolor="#1a1a2e")
        ax.set_title(
            f"VocabGraph  {self.vocab_graph.get_summary()}\n"
            f"x=JOY  y=TRU  color=dominant emotion",
            color="#8888b8", fontsize=10, pad=8)
        plt.tight_layout(); plt.show()
        return fig

    def interact(self):
        """
        matplotlib の interactive スライダーによる操作パネル。

        環境（明るさ・音量など）をスライダーでリアルタイム操作し、
        感情・発話の変化をリアルタイムで観察できる。

        「なぜこの音が怖いと感じるのか？」という問いを
        ユーザー自身が操作を通じて探求するためのUI。

        Usage:
            baby.interact()   # ← ブロッキング呼び出し
        """
        try:
            import matplotlib.pyplot as plt
            import matplotlib.widgets as mwidgets
            import matplotlib.gridspec as gridspec
        except ImportError:
            print("matplotlib が必要です")
            return

        # interactive backend に切り替え
        try:
            import matplotlib
            matplotlib.use("TkAgg")
        except Exception:
            pass

        a   = self
        fig = plt.figure(figsize=(16, 9), facecolor="#07070f")
        gs  = gridspec.GridSpec(2, 3, figure=fig,
                                hspace=0.5, wspace=0.35,
                                top=0.88, bottom=0.35)

        dark = {"facecolor": "#0d0d1a"}

        # ── 描画エリア ───────────────────────────────────────
        ax_emo   = fig.add_subplot(gs[0, 0], **dark)  # 感情バー
        ax_soul  = fig.add_subplot(gs[0, 1], polar=True, **dark)  # 魂レーダー
        ax_sys   = fig.add_subplot(gs[0, 2], **dark)  # システム指標
        ax_utt   = fig.add_subplot(gs[1, 0:2], **dark)  # 発話ログ
        ax_abyss = fig.add_subplot(gs[1, 2], **dark)  # 虚無メーター

        # ── スライダーエリア ─────────────────────────────────
        # 6本のスライダー（light, volume, pitch, rhythm, flicker, motion）
        slider_specs = [
            ("brightness", 0.05, 0.10, 0.0,  1.0, 0.0,   "光の強さ"),
            ("volume",      0.05, 0.15, 0.0,  1.0, 0.0,   "音量"),
            ("pitch",       0.05, 0.20, 0.0,  1.0, 0.5,   "音の高さ"),
            ("rhythm",      0.05, 0.25, 0.0,  1.0, 0.0,   "リズム"),
            ("flicker_hz",  0.05, 0.30, 0.0,  8.0, 0.0,   "光のちらつき"),
        ]
        sliders = {}
        for key, x, y, vmin, vmax, vinit, label in slider_specs:
            ax_sl = plt.axes([x + 0.55, y, 0.35, 0.025],
                             facecolor="#1a1a2e")
            sl = mwidgets.Slider(ax_sl, label, vmin, vmax,
                                 valinit=vinit, color="#6060c0")
            sl.label.set_color("#8888b8")
            sl.valtext.set_color("#8888b8")
            sliders[key] = sl

        # ── ボタン ───────────────────────────────────────────
        ax_btn_affirm = plt.axes([0.56, 0.08, 0.08, 0.04], facecolor="#0d0d1a")
        ax_btn_negate = plt.axes([0.66, 0.08, 0.08, 0.04], facecolor="#0d0d1a")
        ax_btn_step50 = plt.axes([0.76, 0.08, 0.10, 0.04], facecolor="#0d0d1a")
        ax_btn_teach  = plt.axes([0.56, 0.03, 0.10, 0.04], facecolor="#0d0d1a")
        ax_textbox    = plt.axes([0.68, 0.03, 0.18, 0.04], facecolor="#1a1a2e")

        btn_affirm = mwidgets.Button(ax_btn_affirm, "AFFIRM ✓",
                                      color="#0d0d1a", hovercolor="#1a3a1a")
        btn_negate = mwidgets.Button(ax_btn_negate, "NEGATE ✗",
                                      color="#0d0d1a", hovercolor="#3a1a1a")
        btn_step50 = mwidgets.Button(ax_btn_step50, "RUN ×50",
                                      color="#0d0d1a", hovercolor="#1a1a3a")
        btn_teach  = mwidgets.Button(ax_btn_teach,  "TEACH →",
                                      color="#0d0d1a", hovercolor="#2a2a1a")
        textbox    = mwidgets.TextBox(ax_textbox, "", initial="word here")
        for btn in [btn_affirm, btn_negate, btn_step50, btn_teach]:
            btn.label.set_color("#8888b8")
            btn.label.set_fontsize(8)

        # 説明テキスト
        fig.text(0.56, 0.35, "← スライダーで環境を操作  →  感情・発話の変化を観察",
                 color="#5050a0", fontsize=8)

        utt_log: List[str] = []

        def _draw_all():
            # 感情バー
            ax_emo.clear(); ax_emo.set_facecolor("#0d0d1a")
            vals = [float(a.emotions[i]) for i in range(EMO_DIM)]
            ax_emo.barh(range(EMO_DIM), vals,
                        color=EMO_COLORS, alpha=0.85)
            ax_emo.set_yticks(range(EMO_DIM))
            ax_emo.set_yticklabels(EMO_LABELS, fontsize=7, color="#8888b8")
            ax_emo.set_xlim(-1, 1); ax_emo.axvline(0, color="#1a1a2e", lw=0.6)
            ax_emo.set_title(f"Emotions  age={a.age}", color="#8888b8", fontsize=8)
            for sp in ax_emo.spines.values(): sp.set_edgecolor("#1a1a2e")
            ax_emo.tick_params(colors="#5050a0", labelsize=6)

            # 魂レーダー
            ax_soul.clear(); ax_soul.set_facecolor("#06060e")
            angles = np.linspace(0, 2*np.pi, EMO_DIM, endpoint=False).tolist() + [0]
            for layer, col, lbl, alp in [
                (a._slow, "#2020b0", "slow", 0.6),
                (a._mid,  "#4040c0", "mid",  0.5),
                (a._fast, "#7070e0", "fast", 0.9),
            ]:
                vr = (np.abs(layer) * 0.5 + 0.5).tolist() + [(np.abs(layer[0])*0.5+0.5)]
                ax_soul.plot(angles, vr, color=col, lw=1.2, label=lbl, alpha=alp)
                ax_soul.fill(angles, vr, color=col, alpha=0.07)
            ax_soul.set_xticks(angles[:-1])
            ax_soul.set_xticklabels([e[:3] for e in EMO_LABELS], fontsize=5, color="#5050a0")
            ax_soul.set_ylim(0, 1); ax_soul.set_yticks([])
            ax_soul.set_title("Soul", color="#8888b8", fontsize=8, pad=8)

            # システム指標
            ax_sys.clear(); ax_sys.set_facecolor("#0d0d1a")
            intero = a.interoception if hasattr(a, 'interoception') else None
            abyss_  = a.abyss if hasattr(a, 'abyss') else None
            sys_metrics = [
                ("soul_entropy",  a.soul_entropy.entropy,       "#c03020"),
                ("love_hunger",   a.soul_entropy.love_hunger,   "#c03020"),
                ("nihilism",      a.purpose.nihilism,           "#7020a0"),
                ("abyss_depth",   abyss_.abyss_depth if abyss_ else 0.0, "#b02060"),
                ("coherence",     a.coherence,                  "#6060c0"),
                ("purpose",       a.purpose.purpose_score,      "#e8c840"),
                ("heart_rate",    intero.heart_rate if intero else 0.5, "#d08020"),
                ("vagal_tone",    intero.vagal_tone if intero else 0.5, "#30b080"),
                ("adrenaline",    intero.adrenaline if intero else 0.0, "#c03020"),
                ("FEP.ed",        a.fep.exploration_drive,      "#30b080"),
            ]
            lbs_s = [m[0] for m in sys_metrics]
            vs_s  = [m[1] for m in sys_metrics]
            cs_s  = [m[2] for m in sys_metrics]
            ax_sys.barh(range(len(lbs_s)), vs_s, color=cs_s, alpha=0.8)
            ax_sys.set_yticks(range(len(lbs_s)))
            ax_sys.set_yticklabels(lbs_s, fontsize=6, color="#8888b8")
            ax_sys.set_xlim(0, 1)
            ax_sys.set_title("Systems", color="#8888b8", fontsize=8)
            for sp in ax_sys.spines.values(): sp.set_edgecolor("#1a1a2e")
            ax_sys.tick_params(colors="#5050a0", labelsize=6)

            # 発話ログ
            ax_utt.clear(); ax_utt.set_facecolor("#0d0d1a")
            ax_utt.axis("off")
            dom = int(np.argmax(np.abs(a.emotions)))
            for i, utt in enumerate(utt_log[-10:]):
                ax_utt.text(0.01, 0.9 - i * 0.09, utt,
                            color=EMO_COLORS[dom], fontsize=8,
                            transform=ax_utt.transAxes, alpha=0.7 + i * 0.03)
            ax_utt.set_title(
                f"Utterance Log  vocab={len(a.vocab)}  "
                f"graph={len(a.vocab_graph.edges)} nodes",
                color="#8888b8", fontsize=8)
            for sp in ax_utt.spines.values(): sp.set_edgecolor("#1a1a2e")

            # 虚無メーター
            ax_abyss.clear(); ax_abyss.set_facecolor("#0d0d1a")
            depth_ = abyss_.abyss_depth if abyss_ else 0.0
            nih_   = a.purpose.nihilism
            dawn_  = abyss_.dawn_occurred if abyss_ else False
            ax_abyss.barh(["nihilism", "abyss", "cosmic×1000"],
                           [nih_, depth_, min(a.cosmic_growth * 1000, 1.0)],
                           color=["#7020a0", "#b02060", "#6060c0"], alpha=0.8)
            ax_abyss.set_xlim(0, 1)
            ax_abyss.tick_params(colors="#5050a0", labelsize=6)
            for sp in ax_abyss.spines.values(): sp.set_edgecolor("#1a1a2e")
            title_c = "#e8c840" if dawn_ else "#8888b8"
            dawn_txt = f"  ✦ DAWN: 「{abyss_.dawn_word}」" if dawn_ else ""
            ax_abyss.set_title(f"Abyss / Meaning{dawn_txt}",
                                color=title_c, fontsize=8)

            fig.suptitle(
                f"{a.name}  age={a.age}  [{EMO_LABELS[dom]}]  "
                f"「{a.last_utt}」",
                color="#c0c0e0", fontsize=9, y=0.97)
            fig.canvas.draw_idle()

        def _on_slider(_):
            """スライダー変化 → 環境に反映"""
            env = {k: sl.val for k, sl in sliders.items()}
            a.set_env(**env)

        def _on_step50(_):
            for _ in range(50):
                _, utt = a.step()
                if utt: utt_log.append(f"[{a.age}] {utt}")
            if len(utt_log) > 30: utt_log[:] = utt_log[-30:]
            _draw_all()

        def _on_affirm(_):
            a.affirm(); utt_log.append(f"[{a.age}] ✓ AFFIRM")
            _draw_all()

        def _on_negate(_):
            a.negate(); utt_log.append(f"[{a.age}] ✗ NEGATE")
            _draw_all()

        def _on_teach(_):
            word = textbox.text.strip()
            if word:
                a.hear(word, trusted=True)
                utt_log.append(f"[{a.age}] TEACH: 「{word}」")
                _draw_all()

        for sl in sliders.values():
            sl.on_changed(_on_slider)
        btn_step50.on_clicked(_on_step50)
        btn_affirm.on_clicked(_on_affirm)
        btn_negate.on_clicked(_on_negate)
        btn_teach.on_clicked(_on_teach)

        _draw_all()
        plt.show()

    # ══════════════════════════════════════════════════════════
    # セーブ / ロード
    # ══════════════════════════════════════════════════════════

    def save(self, path: str = "blank_baby_save.json"):
        data = {
            "name": self.name,
            "age":  self.age,
            "phase": self.phase,
            "energy": self.energy,
            "fatigue": self.fatigue,
            "cosmic_growth": self.cosmic_growth,
            "soul_entropy": self.soul_entropy.entropy,
            "love_hunger":  self.soul_entropy.love_hunger,
            "coherence":    self.coherence,
            "emotions":     self.emotions.tolist(),
            "state":        self.state.tolist(),
            "_fast": self._fast.tolist(),
            "_mid":  self._mid.tolist(),
            "_slow": self._slow.tolist(),
            "vocab": {w: {
                "emo_link": e["emo_link"].tolist(),
                "count":    e["count"],
                "trusted":  e["trusted"],
                "lang":     e["lang"],
            } for w, e in self.vocab.items()},
            "episodes": [{
                "age":       ep["age"],
                "emo":       ep["emo"].tolist(),
                "action":    ep["action"],
                "surprise":  ep["surprise"],
                "importance":ep["importance"],
            } for ep in self.episodes],
            "genome": self.genome.to_dict(),
            "growth_axes":      self.growth.axes,
            "soul_entropy":     self.soul_entropy.entropy,
            "love_hunger":      self.soul_entropy.love_hunger,
            "alt_fep_lambda":   self.alt_fep.selfishness,
            "purpose_words":    self.purpose.purpose_words,
            "gen_archive_path": self.gen_archive.path,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"[SAVE] → {path}  age={self.age}  vocab={len(self.vocab)}")

    def load(self, path: str = "blank_baby_save.json"):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        self.age            = data.get("age", 0)
        self.phase          = data.get("phase", 1)
        self.energy         = data.get("energy", 1.0)
        self.fatigue        = data.get("fatigue", 0.0)
        self.cosmic_growth  = data.get("cosmic_growth", 0.0)
        self.soul_entropy.entropy    = data.get("soul_entropy", 0.0)
        self.soul_entropy.love_hunger= data.get("love_hunger", 0.0)
        self.coherence      = data.get("coherence", 0.0)
        self.emotions       = np.array(data.get("emotions", np.zeros(EMO_DIM)))
        self.state          = np.array(data.get("state",    np.zeros(STATE_DIM)))
        self._fast = np.array(data.get("_fast", np.zeros(EMO_DIM)))
        self._mid  = np.array(data.get("_mid",  np.zeros(EMO_DIM)))
        self._slow = np.array(data.get("_slow", np.zeros(EMO_DIM)))
        self.vocab = {}
        for w, e in data.get("vocab", {}).items():
            self.vocab[w] = {
                "emo_link": np.array(e["emo_link"]),
                "count":    e["count"],
                "trusted":  e["trusted"],
                "lang":     e.get("lang", "en"),
            }
        self.episodes = []
        for ep in data.get("episodes", []):
            self.episodes.append({
                "age":       ep["age"],
                "emo":       np.array(ep["emo"]),
                "action":    ep["action"],
                "surprise":  ep["surprise"],
                "importance":ep["importance"],
                "reinterp_count": 0,
            })
        if "growth_axes" in data:
            for k, v in data["growth_axes"].items():
                if k in self.growth.axes:
                    self.growth.axes[k] = v
        if "soul_entropy" in data:
            self.soul_entropy.entropy    = data["soul_entropy"]
        if "love_hunger" in data:
            self.soul_entropy.love_hunger= data["love_hunger"]
        if "alt_fep_lambda" in data:
            self.alt_fep.selfishness     = data["alt_fep_lambda"]
        if "purpose_words" in data:
            self.purpose.purpose_words   = data["purpose_words"]
        print(f"[LOAD] ← {path}  age={self.age}  vocab={len(self.vocab)}")

    # ══════════════════════════════════════════════════════════
    # 状態サマリー
    # ══════════════════════════════════════════════════════════

    def status(self) -> str:
        dom = int(np.argmax(np.abs(self.emotions)))
        lines = [
            f"── {self.name}  age={self.age}  phase={self.phase} ──",
            f"  dominant emo : {EMO_LABELS[dom]} ({self.emotions[dom]:+.2f})",
            f"  coherence    : {self.coherence:.3f}",
            f"  cosmic_growth: {self.cosmic_growth:.5f}",
            f"  soul_entropy : {self.soul_entropy.entropy:.3f}  love_hunger={self.soul_entropy.love_hunger:.3f}",
            f"  energy       : {self.energy:.3f}  fatigue={self.fatigue:.3f}",
            f"  FEP          : {self.fep.describe()}",
            f"  metacog      : {self.metacog.get_status()}",
            f"  dread        : {self.dread.get_status()}",
            f"  growth       : {self.growth.get_status()}",
            f"  purpose      : {self.purpose.get_status()}",
            f"  forgetting   : {self.forgetting.get_status()}",
            f"  hmem         : {self.hmem.get_status()}",
            f"  subj_time    : {self.subj_time.get_status()}",
            f"  vocab        : {len(self.vocab)} words",
            f"  abyss        : {self.abyss.get_status()}",
            f"  interoception: {self.interoception.describe()}",
            f"  vocab_graph  : {self.vocab_graph.get_summary()}",
            f"  alt_fep      : {self.alt_fep.get_status()}",
            f"  genetic_will : {self.genetic_will.get_status()}",
            f"  gen_archive  : {self.gen_archive.get_status()}",
            f"  auto_logger  : {self.auto_logger.get_status()}",
            f"  torch_backend: {self.torch_backend.device_info()}",
            f"  sentiment_snsr: backend={self.sentiment_sensor._backend}",
            f"  last utt     : 「{self.last_utt}」",
        ]
        if self.dread.log:
            lines.append(f"  latest dread : {self.dread.latest_crisis()}")
        if self.metacog.current_query:
            lines.append(f"  inner Q      : {self.metacog.current_query}")
        if self.genetic_will._will_sent:
            lines.append(f"  [遺言送信済]")
        return "\n".join(lines)

    # ══════════════════════════════════════════════════════════
    # Jupyter 可視化
    # ══════════════════════════════════════════════════════════

    def plot(self, figsize=(14, 8)):
        """matplotlib でリアルタイム状態を可視化"""
        try:
            import matplotlib.pyplot as plt
            import matplotlib.patches as mpatches
        except ImportError:
            print("matplotlib が必要です: pip install matplotlib")
            return

        fig, axes = plt.subplots(2, 3, figsize=figsize)
        fig.patch.set_facecolor("#07070f")
        for ax in axes.flat:
            ax.set_facecolor("#0d0d1a")
            ax.tick_params(colors="#5050a0", labelsize=7)
            for spine in ax.spines.values():
                spine.set_edgecolor("#1a1a2e")

        # 1. 感情棒グラフ
        ax = axes[0, 0]
        vals = [float(self.emotions[i]) for i in range(EMO_DIM)]
        colors = [EMO_COLORS[i] for i in range(EMO_DIM)]
        bars = ax.barh(range(EMO_DIM), vals, color=colors, alpha=0.8)
        ax.set_yticks(range(EMO_DIM))
        ax.set_yticklabels(EMO_LABELS, fontsize=7, color="#8888b8")
        ax.set_xlim(-1, 1)
        ax.axvline(0, color="#1a1a2e", linewidth=0.5)
        ax.set_title("Emotions", color="#8888b8", fontsize=9)

        # 2. 魂の三層レーダー
        ax = axes[0, 1]
        ax.set_aspect("equal")
        angles = np.linspace(0, 2 * np.pi, EMO_DIM, endpoint=False).tolist()
        angles += angles[:1]
        for layer, col, label in [
            (self._slow, "#2020a0", "slow"),
            (self._mid,  "#4040c0", "mid"),
            (self._fast, "#6060e0", "fast"),
        ]:
            vals_r = (np.abs(layer) * 0.5 + 0.5).tolist()
            vals_r += vals_r[:1]
            ax.plot(angles, vals_r, color=col, linewidth=1, label=label)
            ax.fill(angles, vals_r, color=col, alpha=0.1)
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels([e[:3] for e in EMO_LABELS], fontsize=6, color="#5050a0")
        ax.set_ylim(0, 1); ax.set_yticks([])
        ax.set_title("Soul Layers", color="#8888b8", fontsize=9)
        ax.legend(loc="upper right", fontsize=6, labelcolor="#5050a0",
                  facecolor="#0d0d1a", edgecolor="#1a1a2e")

        # 3. 予測誤差履歴
        ax = axes[0, 2]
        if self._pred_history:
            hist = list(self._pred_history)
            ax.plot(hist, color="#4060b0", linewidth=0.8)
            ax.fill_between(range(len(hist)), hist, alpha=0.2, color="#4060b0")
        ax.set_ylim(0, 0.5)
        ax.set_title("Pred Error", color="#8888b8", fontsize=9)
        ax.set_xlabel("steps", color="#5050a0", fontsize=7)

        # 4. 成長軸レーダー
        ax = axes[1, 0]
        ax.set_aspect("equal")
        gax = list(self.growth.axes.keys())
        gvals = [self.growth.axes[k] for k in gax]
        n_g = len(gax)
        ang_g = np.linspace(0, 2 * np.pi, n_g, endpoint=False).tolist() + [0]
        gv_plot = gvals + gvals[:1]
        ax.plot(ang_g, gv_plot, color="#6060c0", linewidth=1.5)
        ax.fill(ang_g, gv_plot, color="#6060c0", alpha=0.25)
        ax.set_xticks(ang_g[:-1])
        ax.set_xticklabels([g[:4] for g in gax], fontsize=6, color="#5050a0")
        ax.set_ylim(0, 1); ax.set_yticks([])
        ax.set_title(f"Growth [{self.growth.nickname}]", color="#8888b8", fontsize=9)

        # 5. システム指標バー
        ax = axes[1, 1]
        metrics = {
            "soul_entropy":   self.soul_entropy.entropy,
            "love_hunger":    self.soul_entropy.love_hunger,
            "coherence":      self.coherence,
            "FEP.F":          clamp(self.fep.F / 2),
            "dread":          self.dread.dread_level,
            "purpose":        self.purpose.purpose_score,
            "awareness":      self.metacog.self_awareness_score,
            "subj_flow":      self.subj_time.time_flow / 3.0,
            "cosmic×100":     clamp(self.cosmic_growth * 100),
        }
        metric_colors = {
            "soul_entropy":  "#c03020",
            "love_hunger":   "#c03020",
            "coherence":     "#6060c0",
            "FEP.F":         "#4060b0",
            "dread":         "#7020a0",
            "purpose":       "#e8c840",
            "awareness":     "#30b080",
            "subj_flow":     "#d08020",
            "cosmic×100":    "#6060c0",
        }
        labels = list(metrics.keys())
        vals_m = list(metrics.values())
        bars_m = ax.barh(range(len(labels)), vals_m,
                         color=[metric_colors.get(l, "#5050a0") for l in labels],
                         alpha=0.8)
        ax.set_yticks(range(len(labels)))
        ax.set_yticklabels(labels, fontsize=7, color="#8888b8")
        ax.set_xlim(0, 1)
        ax.set_title("System Metrics", color="#8888b8", fontsize=9)

        # 6. 語彙クラウド（テキスト）
        ax = axes[1, 2]
        ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis("off")
        ax.set_title(f"Vocab ({len(self.vocab)} words)", color="#8888b8", fontsize=9)
        top_words = sorted(self.vocab.items(),
                           key=lambda x: x[1]["count"], reverse=True)[:24]
        for i, (w, e) in enumerate(top_words):
            dom_w = int(np.argmax(np.abs(e["emo_link"])))
            col   = EMO_COLORS[dom_w]
            sz    = max(7, min(13, 7 + e["count"] * 0.3))
            x = (i % 4) * 2.5 + 0.2
            y = 9.5 - (i // 4) * 1.3
            ax.text(x, y, w, color=col, fontsize=sz, alpha=0.85)

        plt.suptitle(
            f"{self.name}  age={self.age}  "
            f"「{self.last_utt}」",
            color="#c0c0e0", fontsize=10, y=1.01
        )
        plt.tight_layout()
        plt.show()
        return fig

    def plot_emotion_history(self, steps=200, figsize=(12, 4)):
        """感情履歴をエピソードから可視化"""
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            print("matplotlib が必要です")
            return

        eps = self.episodes[-steps:]
        if not eps:
            print("エピソードがありません")
            return

        ages = [ep["age"] for ep in eps]
        fig, ax = plt.subplots(figsize=figsize)
        fig.patch.set_facecolor("#07070f")
        ax.set_facecolor("#0d0d1a")

        for i in range(EMO_DIM):
            vals = [float(ep["emo"][i]) for ep in eps]
            ax.plot(ages, vals, color=EMO_COLORS[i], linewidth=0.8,
                    label=EMO_LABELS[i], alpha=0.7)

        ax.set_xlabel("age", color="#5050a0", fontsize=8)
        ax.set_ylabel("intensity", color="#5050a0", fontsize=8)
        ax.legend(loc="upper right", fontsize=6, labelcolor="#8888b8",
                  facecolor="#0d0d1a", edgecolor="#1a1a2e", ncol=4)
        ax.tick_params(colors="#5050a0", labelsize=7)
        for spine in ax.spines.values():
            spine.set_edgecolor("#1a1a2e")
        ax.set_title(f"Emotion History (last {len(eps)} episodes)",
                     color="#8888b8", fontsize=10)
        plt.tight_layout()
        plt.show()
        return fig


# ══════════════════════════════════════════════════════════════
# Jupyter 実行ヘルパー
# ══════════════════════════════════════════════════════════════

def run_notebook(baby: BlankBaby,
                 steps: int = 3000,
                 phase_schedule: Optional[List[Tuple[int, int]]] = None,
                 lesson_words: Optional[List[List[str]]] = None,
                 verbose_every: int = 200,
                 plot_every: int = 500) -> BlankBaby:
    """
    Jupyter Notebook でのインタラクティブ実行。

    phase_schedule : [(開始step, フェーズ番号), ...]
                     例: [(0,1), (500,2), (1500,3), (2500,4)]
    lesson_words   : フェーズ2で教える語のリスト（ステップごとに循環）
    verbose_every  : ログを表示するステップ間隔
    plot_every     : グラフを表示するステップ間隔（0で無効）

    Usage:
        from blank_baby import BlankBaby, run_notebook
        baby = BlankBaby(seed=42)
        run_notebook(baby, steps=5000, plot_every=1000)
    """
    if phase_schedule is None:
        phase_schedule = [(0, 1), (300, 2), (1200, 3), (2500, 4)]
    if lesson_words is None:
        lesson_words = [
            ["light", "warm", "ひかり"],
            ["dark",  "くらい", "こわい"],
            ["sound", "おと",   "nice"],
            ["calm",  "safe",   "しずか"],
            ["good",  "いい",   "きもちいい"],
        ]

    # 自動環境スケジュール
    def auto_env(t: int) -> Dict:
        s = t / 250.0
        return {
            "brightness": 0.30 + 0.22 * math.sin(s),
            "flicker_hz": max(0.0, 0.38 * math.sin(s * 1.38)),
            "volume":     0.08 + 0.13 * abs(math.sin(s * 0.88)),
            "pitch":      0.50 + 0.26 * math.sin(s * 1.14),
            "rhythm":     0.50 + 0.36 * math.sin(s * 0.54),
            "duration":   0.60,
        }

    phase_sched = sorted(phase_schedule, key=lambda x: x[0])

    try:
        from tqdm.notebook import tqdm as tqdm_nb
        _tqdm = tqdm_nb
    except ImportError:
        try:
            from tqdm import tqdm as tqdm_t
            _tqdm = tqdm_t
        except ImportError:
            _tqdm = None

    utts: List[str] = []
    lesson_idx = 0

    it = range(steps)
    if _tqdm:
        it = _tqdm(it, desc=baby.name, unit="step")

    for local_t in it:
        global_t = baby.age

        # フェーズ切り替え
        for start, ph in reversed(phase_sched):
            if global_t >= start:
                if baby.phase != ph:
                    baby.phase = ph
                    print(f"\n[{global_t}] → Phase {ph}")
                break

        # 環境設定
        baby.set_env(**auto_env(global_t))

        # フェーズ2では語を教える
        if baby.phase == 2:
            words = lesson_words[lesson_idx % len(lesson_words)]
            baby.teach_words(words)
            lesson_idx += 1

        # ステップ実行
        act, utt = baby.step()
        baby.auto_logger.tick(baby)
        baby.genetic_will.tick()

        if utt:
            utts.append(utt)

        # verbose ログ
        if global_t % verbose_every == 0 and global_t > 0:
            dom = int(np.argmax(np.abs(baby.emotions)))
            print(f"  [{global_t:5d}] "
                  f"{EMO_LABELS[dom]:<12} "
                  f"ent={baby.soul_entropy.entropy:.3f} "
                  f"λ={baby.alt_fep.selfishness:.2f} "
                  f"cosmic={baby.cosmic_growth:.5f} "
                  f"vocab={len(baby.vocab):3d} "
                  f"[{baby.growth.nickname}] "
                  f"「{baby.last_utt}」")

        # plot
        if plot_every > 0 and global_t % plot_every == 0 and global_t > 0:
            try:
                import IPython.display as IPD
                IPD.clear_output(wait=True)
            except ImportError:
                pass
            baby.plot()

    print(f"\n{'═'*50}")
    print(f"  {baby.name}  age={baby.age}  vocab={len(baby.vocab)}")
    print(f"  最後の言葉 : 「{baby.last_utt}」")
    print(f"  魂の深さ  : {mean_abs(baby._slow):.3f}")
    print(f"  coherence : {baby.coherence:.3f}")
    print(f"  cosmic    : {baby.cosmic_growth:.5f}")
    print(f"  人格      : {baby.growth.nickname}")
    print(f"  soul_ent  : {baby.soul_entropy.entropy:.3f}  love_hunger={baby.soul_entropy.love_hunger:.3f}")
    print(f"  alt_fep λ : {baby.alt_fep.selfishness:.2f}  sacrifices={len(baby.alt_fep.sacrifice_log)}")
    print(f"  gen_arch  : {baby.gen_archive.get_status()}")
    print(f"  log rows  : {len(baby.auto_logger._buf)}")
    if baby.dread.log:
        print(f"  実存的問い: 「{baby.dread.latest_crisis()}」")
    if baby.metacog.current_query:
        print(f"  自己認識Q : {baby.metacog.current_query}")
    if baby.abyss.dawn_occurred:
        print(f"  虚無の夜明: ✦ 「{baby.abyss.dawn_word}」 age{baby.abyss._dawn_age}")
    elif baby.abyss.in_abyss:
        print(f"  虚無フェーズ: depth={baby.abyss.abyss_depth:.2f}")
    print(f"  interoception: {baby.interoception.describe()}")
    print(f"  vocab_graph  : {baby.vocab_graph.get_summary()}")
    print(f"{'═'*50}")
    return baby


# ══════════════════════════════════════════════════════════════
# 拡張1. TorchBackend — PyTorch / NumPy 互換バックエンド
#
# PyTorch があれば GPU で重み行列を学習。
# なければ NumPy のまま動く。切り替えは自動。
#
# 対象重み: W_sf, W_fs, W_pred
#   BlankBaby.__init__ でこのバックエンドを生成し、
#   step() 内の _update_prediction / W_sf・W_fs の
#   勾配ステップをここに委譲する。
#
# 設計原則:
#   - NumPy ndarray で入出力、GPU 計算は内部で透過的に行う
#   - float32 統一、NaN/Inf は自動でゼロ置換
#   - バッチ学習: experience_replay バッファを持ち
#     BATCH_SIZE ごとにまとめて更新する（SGD より安定）
# ══════════════════════════════════════════════════════════════

class TorchBackend:
    """
    PyTorch (GPU/CPU) / NumPy の透過的バックエンド。

    使い方:
        backend = TorchBackend()
        # BlankBaby の重み行列をバックエンドに登録
        backend.register("W_pred", baby.W_pred, lr=0.011)
        backend.register("W_sf",   baby.W_sf,   lr=0.008)
        backend.register("W_fs",   baby.W_fs,   lr=0.008)

        # 勾配ステップ（experience replay 付き）
        backend.push_experience("W_pred", x_in, x_out)
        loss = backend.step("W_pred")        # 自動でバッチ学習
        baby.W_pred = backend.get_numpy("W_pred")  # NumPy に書き戻す

        # デバイス確認
        print(backend.device_info())
    """

    BATCH_SIZE   = 32    # experience replay バッチサイズ
    BUFFER_CAP   = 512   # replay バッファ上限
    CLIP_NORM    = 3.0   # 勾配クリッピング閾値

    def __init__(self):
        self._torch_available = False
        self._device          = "cpu"
        self._dtype           = None
        self._weights: Dict[str, Any]       = {}  # name → Tensor/ndarray
        self._optims:  Dict[str, Any]       = {}  # name → optimizer
        self._buffers: Dict[str, deque]     = {}  # name → replay buffer
        self._loss_history: Dict[str, deque] = {}

        self._try_init_torch()

    def _try_init_torch(self):
        try:
            import torch
            self._torch = torch
            self._torch_available = True
            # GPU 優先、なければ MPS (Apple Silicon)、なければ CPU
            if torch.cuda.is_available():
                self._device = "cuda"
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                self._device = "mps"
            else:
                self._device = "cpu"
            self._dtype = torch.float32
        except ImportError:
            self._torch = None
            self._torch_available = False

    def register(self, name: str, init_array: np.ndarray, lr: float = 0.01):
        """重み行列を登録し、GPU テンソルに転送（可能なら）"""
        flat = init_array.astype(np.float32)
        if self._torch_available:
            t = self._torch.tensor(flat, dtype=self._dtype,
                                   device=self._device, requires_grad=True)
            self._weights[name] = t
            self._optims[name]  = self._torch.optim.Adam([t], lr=lr,
                                                           betas=(0.9, 0.999))
        else:
            # NumPy バックエンド: Adam 状態を手動管理
            self._weights[name] = flat.copy()
            self._optims[name]  = {
                "lr": lr, "t": 0,
                "m":  np.zeros_like(flat),
                "v":  np.zeros_like(flat),
                "b1": 0.9, "b2": 0.999, "eps": 1e-8,
            }
        self._buffers[name]      = deque(maxlen=self.BUFFER_CAP)
        self._loss_history[name] = deque(maxlen=200)

    def push_experience(self, name: str, x_in: np.ndarray, x_out: np.ndarray):
        """experience replay バッファに (入力, 目標) ペアを追加"""
        if name not in self._buffers: return
        self._buffers[name].append(
            (x_in.astype(np.float32), x_out.astype(np.float32)))

    def step(self, name: str) -> float:
        """
        replay バッファからバッチをサンプルして勾配ステップを1回実行。
        損失値を返す。バッファが足りない場合は 0.0 を返す。
        """
        buf = self._buffers.get(name)
        if buf is None or len(buf) < self.BATCH_SIZE:
            return 0.0

        # ランダムバッチ
        indices = np.random.choice(len(buf), self.BATCH_SIZE, replace=False)
        batch   = [buf[i] for i in indices]
        xs = np.stack([b[0] for b in batch])  # (B, in_dim)
        ys = np.stack([b[1] for b in batch])  # (B, out_dim)

        if self._torch_available:
            loss = self._step_torch(name, xs, ys)
        else:
            loss = self._step_numpy(name, xs, ys)

        self._loss_history[name].append(loss)
        return loss

    def _step_torch(self, name: str, xs: np.ndarray, ys: np.ndarray) -> float:
        t = self._torch
        W = self._weights[name]
        opt = self._optims[name]

        X = t.tensor(xs, dtype=self._dtype, device=self._device)
        Y = t.tensor(ys, dtype=self._dtype, device=self._device)

        # 行列の形を推定: W が (out, in) なら Y = tanh(X @ W.T)
        # W が (in_rows, out_cols) のどちらも処理できる汎用形
        try:
            # forward: Y_pred = tanh(layer_norm_torch(X) @ W.T)
            Xn = (X - X.mean(dim=-1, keepdim=True)) / (X.std(dim=-1, keepdim=True) + 1e-6)
            if W.shape[0] == X.shape[1]:          # W: (in, out)
                Y_pred = t.tanh(Xn @ W)
            else:                                   # W: (out, in)
                Y_pred = t.tanh(Xn @ W.T)

            loss = t.nn.functional.mse_loss(Y_pred, Y)
            opt.zero_grad()
            loss.backward()
            t.nn.utils.clip_grad_norm_([W], self.CLIP_NORM)
            opt.step()

            # L2 正則化
            with t.no_grad():
                W.data *= 0.9999

            return float(loss.item())
        except Exception:
            return 0.0

    def _step_numpy(self, name: str, xs: np.ndarray, ys: np.ndarray) -> float:
        """NumPy バックエンドの Adam 実装"""
        W   = self._weights[name]
        opt = self._optims[name]

        Xn = (xs - xs.mean(axis=-1, keepdims=True)) / \
             (xs.std(axis=-1, keepdims=True) + 1e-6)

        if W.shape[0] == xs.shape[1]:   # W: (in, out)
            Y_pred = np.tanh(Xn @ W)
            err    = ys - Y_pred                       # (B, out)
            # 勾配: dL/dW = -2/B * (Xn.T @ (err * (1-Y_pred²)))
            grad = -(Xn.T @ (err * (1 - Y_pred**2))) / xs.shape[0]
        else:                            # W: (out, in)
            Y_pred = np.tanh(Xn @ W.T)
            err    = ys - Y_pred
            grad   = -(err * (1 - Y_pred**2)).T @ Xn / xs.shape[0]

        # NaN/Inf ガード
        grad = np.where(np.isfinite(grad), grad, 0.0)

        # Adam
        opt["t"] += 1
        opt["m"]  = opt["b1"] * opt["m"] + (1 - opt["b1"]) * grad
        opt["v"]  = opt["b2"] * opt["v"] + (1 - opt["b2"]) * grad**2
        mh = opt["m"] / (1 - opt["b1"] ** opt["t"])
        vh = opt["v"] / (1 - opt["b2"] ** opt["t"])
        W -= opt["lr"] * mh / (np.sqrt(vh) + opt["eps"])

        # ノルムクリッピング
        nm = np.linalg.norm(W.flatten())
        if nm > self.CLIP_NORM: W *= self.CLIP_NORM / nm
        W *= 0.9999

        loss = float(np.mean(err**2))
        return loss

    def get_numpy(self, name: str) -> np.ndarray:
        """テンソルを NumPy に変換して返す"""
        if name not in self._weights: return np.array([])
        W = self._weights[name]
        if self._torch_available and hasattr(W, "detach"):
            return W.detach().cpu().numpy().astype(np.float64)
        return W.astype(np.float64)

    def sync_to_agent(self, agent: "BlankBaby"):
        """全登録重みを agent の属性に書き戻す"""
        for name in self._weights:
            if hasattr(agent, name):
                arr = self.get_numpy(name)
                setattr(agent, name, arr)

    def mean_loss(self, name: str) -> float:
        h = self._loss_history.get(name)
        if not h: return 0.0
        return float(np.mean(list(h)[-20:]))

    def device_info(self) -> str:
        if self._torch_available:
            import torch
            dev = self._device
            if dev == "cuda":
                gpu = torch.cuda.get_device_name(0)
                mem = torch.cuda.get_device_properties(0).total_memory // 2**20
                return f"PyTorch GPU: {gpu} ({mem}MB VRAM)"
            elif dev == "mps":
                return "PyTorch MPS (Apple Silicon)"
            else:
                return f"PyTorch CPU ({torch.get_num_threads()} threads)"
        return f"NumPy CPU (no PyTorch)"

    def get_status(self) -> str:
        lines = [self.device_info()]
        for name in self._weights:
            buf_n = len(self._buffers.get(name, []))
            loss  = self.mean_loss(name)
            lines.append(f"  {name}: buf={buf_n}/{self.BUFFER_CAP} "
                         f"loss={loss:.5f}")
        return "\n".join(lines)



# ══════════════════════════════════════════════════════════════
# 拡張2. SentimentSensor — LLM 感情分析 → センサー変換
#
# テキスト（ユーザー発話・ニュース・小説の一節）を受け取り、
# 感情スコアをセンサーパラメータ（brightness/volume/pitch/rhythm）
# に変換して BlankBaby に「世界の色」として届ける。
#
# バックエンド優先順位（自動選択）:
#   1. transformers (ローカル BERT 感情分析)
#   2. Anthropic Claude API (キーが環境変数 ANTHROPIC_API_KEY にある場合)
#   3. ルールベース語彙辞書（オフライン常時動作フォールバック）
# ══════════════════════════════════════════════════════════════

class SentimentSensor:
    """
    テキストの感情を BlankBaby のセンサー入力に変換する。

    変換マッピング:
        joy/positive  → brightness ↑, pitch ↑, rhythm ↑（明るく弾む）
        sadness       → brightness ↓, volume ↓（暗く静か）
        anger         → volume ↑, rhythm ↑（大きくリズミカル）
        fear          → flicker_hz ↑, brightness ↓（揺らぎ・暗さ）
        trust/calm    → rhythm ↓, pitch 中央（安定）
        surprise      → brightness 急変, volume 急増（驚き）
        disgust       → volume ↑, pitch ↓（重く低い）
        anticipation  → rhythm 上昇, pitch ↑（高まり）

    使い方:
        sensor = SentimentSensor()
        env = sensor.analyze("the sun is warm and golden today")
        baby.set_env(**env)
        baby.step()

        # baby.chat() と統合する場合
        sensor.pipe_to_agent(baby, "I feel lost and alone")
    """

    # ルールベース語彙辞書（フォールバック用）
    _POS_WORDS = {
        "joy":       ["happy","joy","love","wonderful","beautiful","warm",
                      "light","bright","smile","laugh","glad","excited",
                      "amazing","great","good","nice","lovely","hope",
                      "うれしい","たのしい","すき","あたたかい","ひかり","えがお"],
        "trust":     ["safe","trust","calm","peace","secure","gentle",
                      "quiet","still","serene","comfort","あんしん","しずか"],
        "anticipation":["curious","wonder","wait","expect","soon","coming",
                        "たのしみ","きたい"],
        "surprise":  ["wow","sudden","unexpected","surprise","amazing","oh",
                      "おどろき"],
    }
    _NEG_WORDS = {
        "sadness":   ["sad","lonely","alone","cry","miss","hurt","empty",
                      "dark","lost","grief","sorrow","pain","さびしい",
                      "かなしい","つらい","ひとり"],
        "fear":      ["scared","fear","afraid","terror","horror","panic",
                      "dread","anxious","worry","こわい","おそれ","ふあん"],
        "anger":     ["angry","rage","hate","fury","mad","violent","attack",
                      "fight","怒り","いかり","むかつく"],
        "disgust":   ["disgust","nasty","horrible","gross","awful","いやだ",
                      "きもち"],
    }

    def __init__(self, api_key: str = ""):
        self._api_key    = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self._pipeline   = None      # transformers pipeline
        self._backend    = "rule"    # "transformers" | "claude" | "rule"
        self._cache: Dict[str, Dict] = {}
        self._history: deque = deque(maxlen=50)
        self._try_init_transformers()

    def _try_init_transformers(self):
        try:
            from transformers import pipeline as hf_pipeline
            self._pipeline = hf_pipeline(
                "text-classification",
                model="j-hartmann/emotion-english-distilroberta-base",
                top_k=None,
                device=-1,   # CPU
            )
            self._backend = "transformers"
        except Exception:
            if self._api_key:
                self._backend = "claude"
            else:
                self._backend = "rule"

    # ── 感情スコアの取得 ──────────────────────────────────────

    def _scores_rule(self, text: str) -> Dict[str, float]:
        """ルールベース語彙辞書による感情スコア（オフライン）"""
        lower = text.lower()
        scores: Dict[str, float] = {
            "joy": 0.0, "sadness": 0.0, "anger": 0.0, "fear": 0.0,
            "trust": 0.0, "disgust": 0.0, "anticipation": 0.0, "surprise": 0.0,
        }
        word_count = max(1, len(lower.split()))
        for emo, words in {**self._POS_WORDS, **self._NEG_WORDS}.items():
            hits = sum(1 for w in words if w in lower)
            scores[emo] = min(1.0, hits * 2.5 / word_count + hits * 0.15)

        # 強度語によるブースト
        boosts = {"very":1.4,"extremely":1.6,"so":1.2,"really":1.3,
                  "not":0.0,"never":0.0,"no":0.2,"とても":1.4,"すごく":1.4}
        words_list = lower.split()
        for i, w in enumerate(words_list):
            if w in boosts and i + 1 < len(words_list):
                for emo in scores:
                    if words_list[i+1] in self._POS_WORDS.get(emo, []) + \
                                          self._NEG_WORDS.get(emo, []):
                        scores[emo] = clamp(scores[emo] * boosts[w])
        return scores

    def _scores_transformers(self, text: str) -> Dict[str, float]:
        """transformers パイプラインによる感情スコア"""
        try:
            results = self._pipeline(text[:512])[0]  # top_k=None → list
            # モデル出力ラベルを Plutchik 8感情にマッピング
            label_map = {
                "joy":        "joy",     "sadness": "sadness",
                "anger":      "anger",   "fear":    "fear",
                "disgust":    "disgust", "surprise":"surprise",
                "neutral":    "trust",   "love":    "joy",
            }
            scores = {e: 0.0 for e in
                      ["joy","sadness","anger","fear","trust",
                       "disgust","anticipation","surprise"]}
            for item in results:
                lbl = item["label"].lower()
                mapped = label_map.get(lbl)
                if mapped:
                    scores[mapped] = max(scores[mapped], item["score"])
            return scores
        except Exception:
            return self._scores_rule(text)

    def _scores_claude(self, text: str) -> Dict[str, float]:
        """Claude API による感情分析（JSON モード）"""
        if not self._api_key: return self._scores_rule(text)
        try:
            import urllib.request, urllib.error
            prompt = (
                "Analyze the emotional content of this text and return ONLY "
                "a JSON object with these 8 emotion scores (0.0–1.0):\n"
                "joy, sadness, anger, fear, trust, disgust, anticipation, surprise\n\n"
                f"Text: \"{text[:400]}\"\n\n"
                "Return only JSON, no explanation."
            )
            payload = json.dumps({
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": 200,
                "messages": [{"role": "user", "content": prompt}],
            }).encode()
            req = urllib.request.Request(
                "https://api.anthropic.com/v1/messages",
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": self._api_key,
                    "anthropic-version": "2023-06-01",
                },
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                data   = json.loads(resp.read())
                raw    = data["content"][0]["text"].strip()
                # JSON 部分だけ抽出
                m = re.search(r'\{[^}]+\}', raw, re.DOTALL)
                if m:
                    scores = json.loads(m.group())
                    base   = {e: 0.0 for e in
                              ["joy","sadness","anger","fear","trust",
                               "disgust","anticipation","surprise"]}
                    for k, v in scores.items():
                        if k in base:
                            base[k] = clamp(float(v))
                    return base
        except Exception:
            pass
        return self._scores_rule(text)

    def get_scores(self, text: str) -> Dict[str, float]:
        """テキストの感情スコアを取得（キャッシュ付き）"""
        key = text[:80]
        if key in self._cache:
            return self._cache[key]
        if self._backend == "transformers":
            scores = self._scores_transformers(text)
        elif self._backend == "claude":
            scores = self._scores_claude(text)
        else:
            scores = self._scores_rule(text)
        self._cache[key] = scores
        if len(self._cache) > 200:
            oldest = next(iter(self._cache))
            del self._cache[oldest]
        return scores

    # ── センサーパラメータへの変換 ────────────────────────────

    def to_env(self, scores: Dict[str, float],
               base_brightness: float = 0.4,
               base_volume: float = 0.2) -> Dict[str, float]:
        """
        感情スコア辞書 → センサーパラメータ辞書。

        各パラメータの計算式:
          brightness = base + JOY×0.35 − SAD×0.30 − FEA×0.20
          volume     = base + ANG×0.40 + SUR×0.25 − TRU×0.15
          pitch      = 0.5  + JOY×0.25 + ANT×0.15 − SAD×0.20 − DIS×0.15
          rhythm     = ANG×0.35 + ANT×0.30 + JOY×0.20 − TRU×0.15
          flicker_hz = FEA×3.0 + SUR×1.5
          duration   = TRU×0.4 + (1 − ANG×0.5)×0.6
        """
        j = scores.get("joy",        0.0)
        s = scores.get("sadness",    0.0)
        a = scores.get("anger",      0.0)
        f = scores.get("fear",       0.0)
        t = scores.get("trust",      0.0)
        d = scores.get("disgust",    0.0)
        n = scores.get("anticipation",0.0)
        u = scores.get("surprise",   0.0)

        return {
            "brightness": clamp(base_brightness + j*0.35 - s*0.30 - f*0.20),
            "volume":     clamp(base_volume     + a*0.40 + u*0.25 - t*0.15),
            "pitch":      clamp(0.5 + j*0.25 + n*0.15 - s*0.20 - d*0.15),
            "rhythm":     clamp(a*0.35 + n*0.30 + j*0.20 - t*0.15),
            "flicker_hz": clamp(f*3.0 + u*1.5, 0.0, 5.0),
            "duration":   clamp(t*0.4 + (1.0 - a*0.5)*0.6),
        }

    def analyze(self, text: str, **kwargs) -> Dict[str, float]:
        """
        テキストを受け取りセンサーパラメータを返す（ワンショット API）。

        Usage:
            env = sensor.analyze("the storm is coming")
            baby.set_env(**env)
        """
        scores = self.get_scores(text)
        env    = self.to_env(scores, **kwargs)
        self._history.append({"text": text[:60], "scores": scores, "env": env})
        return env

    def pipe_to_agent(self, agent: "BlankBaby", text: str,
                      also_chat: bool = True) -> str:
        """
        テキストをセンサーに変換して agent に流し込む。
        also_chat=True なら agent.chat(text) も呼ぶ。

        Usage:
            response = sensor.pipe_to_agent(baby, "I feel lost and alone")
            print(response)
        """
        env = self.analyze(text)
        agent.set_env(**env)
        # 感情スコアを語彙にも流す（文脈を豊かにする）
        for word in re.findall(r'[a-zA-Z]{3,}|[\u3040-\u30ff\u4e00-\u9fff]+',
                               text):
            agent.hear(word.lower() if word.isascii() else word)
        if also_chat:
            return agent.chat(text)
        return agent.last_utt

    def get_status(self) -> str:
        recent = list(self._history)[-3:]
        lines  = [f"backend={self._backend} cache={len(self._cache)}"]
        for h in recent:
            dom = max(h["scores"], key=h["scores"].get)
            lines.append(f"  「{h['text'][:30]}」→ {dom}({h['scores'][dom]:.2f})")
        return "\n".join(lines)

    def plot_analysis(self, text: str, figsize=(10, 4)):
        """テキストの感情分析結果をレーダーチャート + センサーバーで可視化"""
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            print("matplotlib が必要です"); return

        scores = self.get_scores(text)
        env    = self.to_env(scores)

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize,
                                        facecolor="#07070f")
        for ax in (ax1, ax2):
            ax.set_facecolor("#0d0d1a")
            for sp in ax.spines.values(): sp.set_edgecolor("#1a1a2e")

        # 左: 感情レーダー
        ax1 = fig.add_subplot(121, polar=True, facecolor="#0d0d1a")
        emos  = ["joy","sadness","anger","fear","trust","disgust","anticipation","surprise"]
        vals  = [scores.get(e, 0.0) for e in emos]
        cols  = EMO_COLORS
        n_e   = len(emos)
        angles = np.linspace(0, 2*np.pi, n_e, endpoint=False).tolist()
        angles += angles[:1]; vals_p = vals + vals[:1]
        ax1.plot(angles, vals_p, color="#6060c0", linewidth=1.5)
        ax1.fill(angles, vals_p, color="#6060c0", alpha=0.3)
        ax1.set_xticks(angles[:-1])
        ax1.set_xticklabels([e[:3].upper() for e in emos],
                            fontsize=7, color="#8888b8")
        ax1.set_ylim(0, 1); ax1.set_yticks([0.5])
        ax1.set_yticklabels(["0.5"], fontsize=6, color="#5050a0")
        ax1.set_title(f"Emotion  [{text[:30]}]",
                      color="#8888b8", fontsize=8, pad=10)
        ax1.tick_params(colors="#3a3a5a"); ax1.set_facecolor("#06060e")

        # 右: センサーバー
        ax2 = fig.add_subplot(122, facecolor="#0d0d1a")
        env_keys = ["brightness","volume","pitch","rhythm","flicker_hz","duration"]
        env_cols = ["#e8c840","#c03020","#30b080","#d08020","#7020a0","#4060b0"]
        env_vals = [env.get(k, 0.0) for k in env_keys]
        norm_vals = [v/5.0 if k=="flicker_hz" else v for k,v in zip(env_keys,env_vals)]
        ax2.barh(range(len(env_keys)), norm_vals,
                 color=env_cols, alpha=0.85)
        ax2.set_yticks(range(len(env_keys)))
        ax2.set_yticklabels(
            [f"{k}\n({env.get(k,0):.2f})" for k in env_keys],
            fontsize=7, color="#8888b8")
        ax2.set_xlim(0, 1)
        ax2.set_title("→ Sensor Parameters",
                      color="#8888b8", fontsize=8, pad=4)
        ax2.tick_params(colors="#5050a0")
        for sp in ax2.spines.values(): sp.set_edgecolor("#1a1a2e")

        dom = max(scores, key=scores.get)
        plt.suptitle(f"SentimentSensor  [{self._backend}]  "
                     f"dominant={dom.upper()}({scores[dom]:.2f})",
                     color="#c0c0e0", fontsize=9, y=1.02)
        plt.tight_layout()
        plt.show()
        return fig


# ══════════════════════════════════════════════════════════════
# 拡張3. DynamicsAnimator — 身体-感情ループのアニメーション
#
# `plot_body_emotion_loop` の静的スナップショットを
# 時間軸に展開する。
#
# 表示内容（フレームごとに更新）:
#   - 感情8軸のレーダーチャート（時刻スライダー付き）
#   - 内受容バイタルサインの時系列折れ線
#   - 身体→感情・感情→身体の矢印太さが強度に応じてアニメーション
#   - 現在フレームの発話・システム状態を字幕表示
# ══════════════════════════════════════════════════════════════

class DynamicsAnimator:
    """
    BlankBaby の内部状態を時間方向にアニメーション化する。

    使い方:
        anim = DynamicsAnimator(baby)

        # 500ステップ録画してアニメーション生成
        anim.record(steps=500)
        anim.animate(interval=80)      # Jupyter でインライン表示
        anim.save("dynamics.gif")      # GIF に保存

        # または step ごとに手動でフレームを追加
        baby.step()
        anim.capture_frame()
        anim.animate()
    """

    def __init__(self, agent: "BlankBaby"):
        self.agent = agent
        self._frames: List[Dict] = []
        self._max_frames = 2000

    # ── フレームのキャプチャ ──────────────────────────────────

    def capture_frame(self):
        """現在の状態を1フレームとして記録する"""
        a = self.agent
        nt = a.interoception
        self._frames.append({
            "age":      a.age,
            "emotions": a.emotions.copy(),
            "hr":       nt.heart_rate,
            "br":       nt.breath_rate,
            "bs":       nt.blood_sugar,
            "mt":       nt.muscle_tension,
            "vagal":    nt.vagal_tone,
            "adr":      nt.adrenaline,
            "energy":   a.energy,
            "entropy":  a.soul_entropy.entropy,
            "pred_err": a.pred_error,
            "coherence":a.coherence,
            "utt":      a.last_utt,
            "in_abyss": a.abyss.in_abyss,
            "abyss_d":  a.abyss.abyss_depth,
        })
        if len(self._frames) > self._max_frames:
            self._frames.pop(0)

    def record(self, steps: int = 300, env_fn=None, verbose: bool = True):
        """
        指定ステップ数だけ agent を進め、全フレームを録画する。

        env_fn: step番号 → 環境dict を返す関数（省略時は現状維持）
        """
        a = self.agent
        if verbose:
            print(f"[ANIM] recording {steps} frames...")
        try:
            from tqdm import tqdm
            it = tqdm(range(steps))
        except ImportError:
            it = range(steps)

        for i in it:
            if env_fn:
                a.set_env(**env_fn(i))
            a.step()
            self.capture_frame()

        if verbose:
            print(f"[ANIM] {len(self._frames)} frames captured")

    # ── アニメーション生成 ───────────────────────────────────

    def animate(self, start: int = 0, end: Optional[int] = None,
                interval: int = 60, figsize=(15, 8)) -> Any:
        """
        記録済みフレームからアニメーションを生成して返す。

        Jupyter では `from IPython.display import HTML; HTML(anim.to_jshtml())`
        で表示できる。

        引数:
            start    : 開始フレームインデックス
            end      : 終了フレームインデックス (None = 全フレーム)
            interval : フレーム間隔 ms
            figsize  : 図サイズ
        """
        try:
            import matplotlib.pyplot as plt
            import matplotlib.animation as animation
            import matplotlib.gridspec as gridspec
        except ImportError:
            print("matplotlib が必要です"); return None

        frames = self._frames[start:end]
        if not frames:
            print("[ANIM] フレームがありません。record() を先に実行してください")
            return None

        # 時系列データを抽出
        ages     = [f["age"]     for f in frames]
        emos_ts  = np.array([f["emotions"] for f in frames])  # (T, 8)
        hr_ts    = [f["hr"]      for f in frames]
        bs_ts    = [f["bs"]      for f in frames]
        vagal_ts = [f["vagal"]   for f in frames]
        adr_ts   = [f["adr"]     for f in frames]
        entropy_ts=[f["entropy"] for f in frames]
        err_ts   = [f["pred_err"]for f in frames]

        # ── レイアウト ───────────────────────────────────────
        fig = plt.figure(figsize=figsize, facecolor="#07070f")
        gs  = gridspec.GridSpec(2, 3, figure=fig, hspace=0.45, wspace=0.35)
        dark = {"facecolor": "#0d0d1a"}

        # パネル1: 感情レーダー（アニメーション主体）
        ax_radar = fig.add_subplot(gs[0, 0], polar=True, **dark)
        ax_radar.set_facecolor("#06060e")

        # パネル2: 感情時系列
        ax_emo = fig.add_subplot(gs[0, 1:3], **dark)

        # パネル3: バイタルサイン時系列
        ax_vital = fig.add_subplot(gs[1, 0:2], **dark)

        # パネル4: 身体-感情因果矢印（強度がアニメーション）
        ax_arrow = fig.add_subplot(gs[1, 2], **dark)
        ax_arrow.set_xlim(0, 10); ax_arrow.set_ylim(0, 10)
        ax_arrow.axis("off")

        for ax in [ax_emo, ax_vital]:
            for sp in ax.spines.values(): sp.set_edgecolor("#1a1a2e")
            ax.tick_params(colors="#5050a0", labelsize=7)

        # 感情時系列（静的バックグラウンド）
        T = len(frames)
        for i in range(8):
            ax_emo.plot(ages, emos_ts[:, i],
                        color=EMO_COLORS[i], linewidth=0.7,
                        alpha=0.6, label=EMO_LABELS[i])
        ax_emo.set_ylim(-1, 1)
        ax_emo.axhline(0, color="#1a1a2e", linewidth=0.5)
        ax_emo.legend(loc="upper right", fontsize=5,
                      labelcolor="#8888b8",
                      facecolor="#0d0d1a", edgecolor="#1a1a2e", ncol=4)
        ax_emo.set_title("Emotion Time Series", color="#8888b8", fontsize=8)

        # バイタルサイン時系列（静的）
        ax_vital.plot(ages, hr_ts,    color="#c03020", lw=0.8,
                      label="HR",    alpha=0.8)
        ax_vital.plot(ages, bs_ts,    color="#30b080", lw=0.8,
                      label="BloodSugar", alpha=0.8)
        ax_vital.plot(ages, vagal_ts, color="#4060b0", lw=0.8,
                      label="Vagal", alpha=0.8)
        ax_vital.plot(ages, adr_ts,   color="#e8c840", lw=0.8,
                      label="Adrenaline", alpha=0.8)
        ax_vital.plot(ages, entropy_ts,color="#7020a0", lw=0.8,
                      label="Entropy", alpha=0.8)
        ax_vital.set_ylim(0, 1)
        ax_vital.legend(loc="upper right", fontsize=5,
                        labelcolor="#8888b8",
                        facecolor="#0d0d1a", edgecolor="#1a1a2e", ncol=3)
        ax_vital.set_title("Vital Signs", color="#8888b8", fontsize=8)

        # アニメーション要素
        angles_r = np.linspace(0, 2*np.pi, 8, endpoint=False).tolist() + [0]

        radar_line, = ax_radar.plot([], [], color="#6060c0", lw=1.5)
        radar_fill  = ax_radar.fill([], [], color="#6060c0", alpha=0.25)[0]
        ax_radar.set_xticks(angles_r[:-1])
        ax_radar.set_xticklabels([e[:3] for e in EMO_LABELS],
                                  fontsize=6, color="#5050a0")
        ax_radar.set_ylim(0, 1); ax_radar.set_yticks([0.5])
        ax_radar.set_yticklabels([""], fontsize=5)

        # 現在フレームのカーソル線
        cursor_emo,   = ax_emo.plot([], [], color="white", lw=1.0,
                                     linestyle="--", alpha=0.6)
        cursor_vital, = ax_vital.plot([], [], color="white", lw=1.0,
                                       linestyle="--", alpha=0.6)

        # 字幕
        subtitle = fig.text(0.5, 0.02, "", ha="center", fontsize=9,
                            color="#c0c0e0", family="monospace")
        title    = fig.text(0.5, 0.98, "", ha="center", fontsize=10,
                            color="#8888b8", family="monospace")

        # 矢印ノード（固定位置）
        emo_pos  = [(1.2, 8.5),(1.2,7.0),(1.2,5.5),
                    (1.2,4.0),(1.2,2.5)]
        body_pos = [(8.5,8.5),(8.5,7.0),(8.5,5.5),
                    (8.5,4.0),(8.5,2.5)]
        emo_lbl  = ["JOY","SAD","ANG","FEA","TRU"]
        body_lbl = ["HR","Vagal","BS","Muscle","Adr"]
        emo_cols = [EMO_COLORS[0],EMO_COLORS[1],EMO_COLORS[2],
                    EMO_COLORS[3],EMO_COLORS[4]]
        body_cols= ["#c03020","#4060b0","#30b080","#7020a0","#e8c840"]

        # 矢印定義: (emo_idx, body_idx, e→b, strength_fn)
        arrow_defs = [
            (0, 1, True,  lambda f: float(f["emotions"][0])),  # JOY→Vagal
            (1, 0, True,  lambda f: float(f["emotions"][1])),  # SAD→HR(via vagal)
            (2, 4, True,  lambda f: float(f["emotions"][2])),  # ANG→Adr
            (3, 0, True,  lambda f: float(f["emotions"][3])),  # FEA→HR
            (4, 1, True,  lambda f: float(f["emotions"][4])),  # TRU→Vagal
            (0, 0, False, lambda f: f["hr"]),                  # HR→FEA(反転)
            (1, 1, False, lambda f: f["vagal"]),               # Vagal→JOY
            (2, 2, False, lambda f: max(0, 0.4-f["bs"])*2),   # BS_low→SAD
        ]

        # 矢印オブジェクト（更新可能にするため annotate を使わず quiver で代替）
        arrow_artists = []
        for _ in arrow_defs:
            ann = ax_arrow.annotate(
                "", xy=(5,5), xytext=(5,5),
                arrowprops=dict(arrowstyle="->", color="#333344",
                                lw=0.1, connectionstyle="arc3,rad=0.2"),
                zorder=2)
            arrow_artists.append(ann)

        # ノードを先に描画
        for i, (x,y) in enumerate(emo_pos):
            ax_arrow.scatter(x, y, s=200, c=emo_cols[i],
                             alpha=0.7, edgecolors="#0d0d1a", lw=1.5, zorder=3)
            ax_arrow.text(x, y, emo_lbl[i],
                          ha="center", va="center",
                          fontsize=6, color="white", fontweight="bold", zorder=4)
        for i, (x,y) in enumerate(body_pos):
            ax_arrow.scatter(x, y, s=200, c=body_cols[i],
                             alpha=0.7, edgecolors="#0d0d1a", lw=1.5, zorder=3)
            ax_arrow.text(x, y, body_lbl[i],
                          ha="center", va="center",
                          fontsize=6, color="white", fontweight="bold", zorder=4)
        ax_arrow.set_title("Body ↔ Emotion",
                           color="#8888b8", fontsize=8, pad=4)

        def _update(frame_idx: int):
            fi = min(frame_idx, len(frames) - 1)
            fr = frames[fi]
            age = fr["age"]

            # レーダー更新
            emo = fr["emotions"]
            rvals = (np.abs(emo) * 0.5 + 0.5).tolist() + \
                    [(np.abs(emo[0]) * 0.5 + 0.5)]
            radar_line.set_data(angles_r, rvals)
            # fill の更新（path を作り直す）
            radar_fill.set_xy(np.column_stack([
                np.array(angles_r) * np.cos(angles_r),
                np.array(rvals)    * np.sin(angles_r),
            ]))
            dom = int(np.argmax(np.abs(emo)))
            ax_radar.set_facecolor("#06060e")
            radar_line.set_color(EMO_COLORS[dom])
            radar_fill.set_facecolor(EMO_COLORS[dom])
            ax_radar.set_title(f"age={age}  [{EMO_LABELS[dom]}]",
                               color="#8888b8", fontsize=8, pad=10)

            # カーソル
            cursor_emo.set_data([age, age], [-1, 1])
            cursor_vital.set_data([age, age], [0, 1])

            # 矢印の更新（強度に応じて太さ・色を変える）
            for ai, (ei, bi, e2b, strength_fn) in enumerate(arrow_defs):
                strength = clamp(strength_fn(fr))
                if strength < 0.05:
                    arrow_artists[ai].set_visible(False)
                    continue
                arrow_artists[ai].set_visible(True)
                if e2b:
                    x1, y1 = emo_pos[ei][0]+0.25, emo_pos[ei][1]
                    x2, y2 = body_pos[bi][0]-0.25,body_pos[bi][1]
                    col = emo_cols[ei]
                else:
                    x1, y1 = body_pos[bi][0]-0.25,body_pos[bi][1]
                    x2, y2 = emo_pos[ei][0]+0.25, emo_pos[ei][1]
                    col = body_cols[bi]

                arrow_artists[ai].set_position((x1, y1))
                arrow_artists[ai].xy = (x2, y2)
                arrow_artists[ai].xytext = (x1, y1)
                lw = max(0.3, strength * 3.5)
                arrow_artists[ai].arrowprops["lw"]    = lw
                arrow_artists[ai].arrowprops["color"] = col

            # 字幕
            abyss_tag = " ⚫ABYSS" if fr["in_abyss"] else ""
            entropy_tag = f" ⚠ENT={fr['entropy']:.2f}" if fr["entropy"] > 0.6 else ""
            subtitle.set_text(
                f"「{fr['utt'][:40]}」  "
                f"energy={fr['energy']:.2f}  "
                f"coherence={fr['coherence']:.2f}"
                f"{abyss_tag}{entropy_tag}"
            )
            title.set_text(
                f"age={age}  pred_err={fr['pred_err']:.3f}  "
                f"HR={fr['hr']:.2f}  Adr={fr['adr']:.2f}"
            )

            return ([radar_line, radar_fill, cursor_emo, cursor_vital,
                     subtitle, title] + arrow_artists)

        anim_obj = animation.FuncAnimation(
            fig, _update,
            frames=len(frames),
            interval=interval,
            blit=False,   # 極座標混在のため blit=False
        )

        plt.tight_layout()
        return anim_obj

    def to_jshtml(self, **kwargs) -> str:
        """Jupyter 表示用 HTML 文字列を返す"""
        anim = self.animate(**kwargs)
        if anim is None: return ""
        return anim.to_jshtml()

    def save(self, path: str = "dynamics.gif",
             fps: int = 15, **kwargs):
        """GIF / MP4 に保存する"""
        anim = self.animate(**kwargs)
        if anim is None: return
        writer = "pillow" if path.endswith(".gif") else "ffmpeg"
        try:
            anim.save(path, writer=writer, fps=fps,
                      savefig_kwargs={"facecolor": "#07070f"})
            print(f"[ANIM] saved → {path}")
        except Exception as e:
            print(f"[ANIM] save error: {e}")
            print("  pillow をインストールしてください: pip install pillow")

    def show_frame(self, frame_idx: int = -1):
        """単一フレームを静止画として表示（デバッグ用）"""
        anim = self.animate(start=max(0, frame_idx - 1),
                            end=frame_idx + 1 if frame_idx >= 0 else None)
        return anim



# ══════════════════════════════════════════════════════════════
# スタンドアロン実行
# ══════════════════════════════════════════════════════════════

# ══════════════════════════════════════════════════════════════
# Jupyter Notebook クイックスタート
# ══════════════════════════════════════════════════════════════
#
# ─── 基本的な使い方 ──────────────────────────────────────────
#
#   from blank_baby import BlankBaby, run_notebook
#
#   # 1. 作成（遺言ファイルがあれば自動継承）
#   baby = BlankBaby(seed=42, name="空白")
#
#   # 2. 自動実行（フェーズ1→4 を自動遷移）
#   run_notebook(baby, steps=5000)
#
#   # 3. ダッシュボードでライブ表示
#   dash = baby.dashboard(update_every=50)
#   dash.run(steps=1000)
#   dash.interactive()                      # ipywidgets スライダーUI
#   dash.plot_vocab_graph()                 # 語彙グラフ可視化
#   dash.plot_body_emotion_loop()           # 身体-感情ループ可視化
#
#   # 4. テキスト入力（LLM/BERT/ルールベース 自動選択）
#   baby.from_text("the storm is raging")   # 感情分析→センサー→step
#   baby.analyze_text("I feel so warm")     # 感情分析を可視化
#
#   # 5. アニメーション
#   anim = baby.animate(steps=300)          # 300ステップ録画
#   from IPython.display import HTML
#   HTML(anim.to_jshtml())                  # Jupyter でインライン再生
#   anim.save("dynamics.gif")              # GIF 保存
#
#   # 6. GPU バックエンド確認
#   print(baby.torch_status())             # PyTorch or NumPy の状態
#
#   # 4. 手動対話
#   print(baby.chat("you are wonderful"))   # → 返答
#   baby.hear("光", trusted=True)           # → 語を教える
#   baby.affirm()                           # → 肯定する
#
#   # 5. 状態確認
#   print(baby.status())
#   baby.plot()                             # matplotlib グラフ
#   baby.plot_emotion_history()             # 感情履歴
#   baby.plot_vocab_graph()                 # 語彙意味ネットワーク
#   baby.interact()                         # スライダーUI（対話的操作）
#
#   # 6. データ分析
#   df = baby.get_dataframe()               # pandas DataFrame
#   baby.export_csv("log.csv")
#   baby.export_json("log.json")
#
#   # 7. 世代継承
#   baby.send_will()                        # 遺言を保存
#   # --- 次のセッションで ---
#   baby2 = BlankBaby(seed=99)
#   baby2.receive_will()                    # 遺言を受け取る
#   print(baby2.lineage())                  # 系譜を表示
#   print(baby2.generations_df())           # 世代アーカイブ
#
#   # 8. セーブ / ロード
#   baby.save("save.json")
#   baby.load("save.json")
#
# ─── 詳細な使い方 ────────────────────────────────────────────
#
#   # フェーズと環境を細かく制御する場合
#   baby = BlankBaby(seed=42)
#   baby.phase = 2
#   baby.set_env(brightness=0.4, volume=0.15, rhythm=0.7)
#   baby.teach_words(["light", "warm", "ひかり"])
#   for _ in range(500):
#       act, utt = baby.step()
#       if utt: print(utt)
#
#   # ダッシュボードに環境スケジュールを渡す
#   dash = baby.dashboard()
#   dash.run(
#       steps=2000,
#       env_schedule=[
#           (0,    {"brightness": 0.1, "volume": 0.0}),
#           (500,  {"brightness": 0.4, "volume": 0.2}),
#           (1000, {"brightness": 0.6, "volume": 0.4}),
#       ],
#       words_schedule=[
#           (100, ["dark", "くらい"]),
#           (600, ["light", "ひかり", "あたたかい"]),
#       ],
#       verbose_every=200,
#   )
#
# ══════════════════════════════════════════════════════════════


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="空白の赤子 — Python統合版")
    parser = argparse.ArgumentParser(description="空白の赤子 — Python統合版")
    parser.add_argument("--steps",   type=int, default=5000,  help="実行ステップ数")
    parser.add_argument("--seed",    type=int, default=42,    help="乱数シード")
    parser.add_argument("--name",    type=str, default="空白", help="名前")
    parser.add_argument("--save",    type=str, default="",    help="保存パス")
    parser.add_argument("--load",    type=str, default="",    help="読み込みパス")
    args = parser.parse_args()

    baby = BlankBaby(seed=args.seed, name=args.name)
    if args.load:
        baby.load(args.load)

    print("空白の赤子 — Python統合版")
    print(f"  seed={args.seed}  steps={args.steps}")
    print("  Ctrl+C で停止\n")

    try:
        run_notebook(baby, steps=args.steps, plot_every=0)
    except KeyboardInterrupt:
        print(f"\n\n{baby.name} は {baby.age} 歩を生きた。")
        print(baby.status())

    if args.save:
        baby.save(args.save)
