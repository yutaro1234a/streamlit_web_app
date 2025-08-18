# ui_components.py
import streamlit as st
import inspect
from typing import List, Dict, Optional

from __future__ import annotations

def safe_rerun():
    try:
        st.rerun()
    except Exception:
        try:
            st.experimental_rerun()
        except Exception:
            pass

def inject_touch_ui_css():
    st.markdown("""
    <style>
      .stButton>button {
        padding: 16px 14px !important; font-size: 18px !important; font-weight: 800 !important;
        border-radius: 14px !important; min-height: 56px;
      }
      .seg-row { display: grid; grid-auto-flow: column; gap: 8px; }
    </style>
    """, unsafe_allow_html=True)

def segmented_picker(
    label: str,
    options: List[str],
    key: str,
    color_map: Optional[Dict[str, str]] = None,
) -> str:
    """キー衝突しないピル風セグメント（内部で一意キーを自動生成）"""
    cur = st.session_state.get(key, options[0])

    # 呼び出し位置を使って一意な“内部ベースキー”を生成（安定的）
    try:
        caller = inspect.currentframe().f_back
        loc = f"{caller.f_code.co_filename}:{caller.f_lineno}"
    except Exception:
        loc = key
    base = f"{key}__{abs(hash(loc)) % 10**8}"  # 例: score_class_seg__12345678

    st.caption(label)
    cols = st.columns(len(options))

    for i, opt in enumerate(options):
        active = (opt == cur)
        show = f"✅ {opt}" if active else opt
        btn_key = f"{base}_btn_{i}"  # ← 呼び出し毎に base が変わるので衝突しない

        if cols[i].button(show, key=btn_key, use_container_width=True):
            st.session_state[key] = opt
            try:
                st.rerun()
            except Exception:
                try:
                    st.experimental_rerun()
                except Exception:
                    pass

    return st.session_state.get(key, options[0])

def inject_compact_pick_css():
    """ラジオを“極小ピル”にしつつ、選択時は淡色ハイライトで分かりやすく"""
    st.markdown("""
    <style>
      /* ラジオ全体の詰め */
      .stRadio > label { margin-bottom: 2px; font-size: 12px; color:#6b7280; }
      .stRadio { margin-bottom: 4px; }
      div[role="radiogroup"] { gap: 6px !important; }

      /* ピル風の見た目（通常） */
      div[role="radiogroup"] label {
        border: 1px solid #d1d5db;           /* gray-300 */
        border-radius: 999px;
        padding: 6px 10px;
        background: #f8fafc;                  /* slate-50 */
        font-weight: 700;
        font-size: 14px;
        line-height: 1.1;
        transition: background .15s, color .15s, border-color .15s, box-shadow .15s, transform .02s;
      }
      div[role="radiogroup"] label:hover { background:#f1f5f9; } /* slate-100 */
      div[role="radiogroup"] label:active { transform: translateY(1px); }

      /* ✅ 選択時（黒ベタ禁止→淡いブルー帯で強調） */
      /* どちらのDOM構造でも効くように2パターン指定 */
      div[role="radiogroup"] input:checked + div + label,
      div[role="radiogroup"] label:has(input:checked) {
        background: #e8f1ff;                  /* やさしい青ハイライト */
        color: #0f172a;                        /* slate-900 */
        border-color: #3b82f6;                 /* blue-500 */
        box-shadow: 0 0 0 2px rgba(59,130,246,.15) inset; /* 内側うっすら */
      }

      /* アクセシビリティ：フォーカスリング */
      div[role="radiogroup"] input:focus-visible + div + label,
      div[role="radiogroup"] label:has(input:focus-visible) {
        box-shadow: 0 0 0 3px rgba(59,130,246,.25);
      }

      /* セレクトボックスの上下余白も少し詰める */
      .stSelectbox > label { margin-bottom: 2px; font-size: 12px; color:#6b7280; }
      .stSelectbox { margin-bottom: 4px; }
    </style>
    """, unsafe_allow_html=True)

def radio_compact(
    label: str,
    options: List[str],
    key: str,
    *,
    horizontal: bool = True,
    index: Optional[int] = None,
):
    """見た目コンパクトなラジオ（実体は st.radio）"""
    return st.radio(
        label,
        options,
        key=key,
        horizontal=horizontal,
        index=index if index is not None else 0,
    )
