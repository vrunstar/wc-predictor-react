import streamlit as st
from core.db import fixtures_today, res_map, update_after_res, pred_updated, rank_map, form_map
from core.predictor import load_model, predict_match
from core.utils import flag_img, format_kickoff, render_form
import os

ADMIN_SECRET = st.secrets["ADMIN"]
forms = form_map()
ranks = rank_map()

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');            

.page-title {
    font-family:'ChampionGothic',sans-serif; font-weight:900;
    font-size: 5rem;
    letter-spacing: 0.1em;
    color: #F0F0F0;
    margin-bottom: 0.15rem;
}
.field-label {
    font-family: 'Inter', sans-serif;
    font-size: 0.7rem;
    color: #999;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 6px;
    display: block;
}
.match-box {
    background: rgba(10,10,10,0.65);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid #242424;
    border-radius: 8px;
    padding: 0.85rem 0.5rem;
    text-align: center;
    margin-bottom: 1rem;
}
.match-teams {
    font-family: 'ChampionGothic', sans-serif;
    font-size: 1.3rem;
    letter-spacing: 0.08em;
    color: #F0F0F0;
}
.match-meta {
    font-family: 'Inter', sans-serif;
    font-size: 0.7rem;
    color: #444;
    margin-top: 4px;
    letter-spacing: 0.05em;
}
.status-ok {
    background: rgba(76,175,80,0.12);
    border: 1px solid rgba(76,175,80,0.25);
    color: #81c784;
    padding: 10px 14px;
    border-radius: 8px;
    font-family: 'Inter', sans-serif;
    font-size: 0.85rem;
    margin-bottom: 1rem;
}
.status-err {
    background: rgba(244,67,54,0.12);
    border: 1px solid rgba(244,67,54,0.25);
    color: #e57373;
    padding: 10px 14px;
    border-radius: 8px;
    font-family: 'Inter', sans-serif;
    font-size: 0.85rem;
    margin-bottom: 1rem;
}
.stTextInput input {
    background: rgba(10,10,10,0.65) !important;
    border: 1px solid #242424 !important;
    border-radius: 8px !important;
    color: #fff !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.9rem !important;
}
.stNumberInput input {
    background: rgba(10,10,10,0.65) !important;
    border: 1px solid #242424 !important;
    border-radius: 8px !important;
    color: #fff !important;
    font-family: 'Inter', sans-serif !important;
}
div[data-testid="stButton"] button {
    background: rgba(10,10,10,0.65) !important;
    backdrop-filter: blur(14px) !important;
    border: 1px solid #242424 !important;
    border-radius: 8px !important;
    color: #F0F0F0 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: clamp(0.65rem, 2.5vw, 1rem) !important;
    letter-spacing: 0.05em !important;
    padding: 0.6rem !important;
    width: 100% !important;
    white-space: nowrap !important;
    transition: all 0.15s !important;
}
div[data-testid="stButton"] button:hover {
    border-color: #FFD700 !important;
    color: #FFD700 !important;
    background: rgba(10,10,10,0.65) !important;
    font-family: 'Inter', sans-serif !important;
}
.fix-card {
    background: rgba(10,10,10,0.65);
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    border-radius: 10px;
    border: 1px solid #242424;
    padding: 1.1rem 1.4rem;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="page-title">ADMIN</div>', unsafe_allow_html=True)

_, col, _ = st.columns([0.1, 3, 0.1])
with col:

    # ── First incomplete match today ──────────────────────────────────────────
    fixtures = fixtures_today()
    incomplete = [fx for fx in fixtures if not res_map(fx["match_id"])]


    if not incomplete:
        st.markdown('<div class="match-box"><div class="match-meta">No incomplete matches today</div></div>', unsafe_allow_html=True)
        fx = None
    else:
        fx        = incomplete[0]
        home      = fx.get("home") or {}
        away      = fx.get("away") or {}
        home_code = home.get("team_code", "???")
        away_code = away.get("team_code", "???")
        home_id   = home.get("team_id")
        away_id   = away.get("team_id")
        group     = fx.get("group_name", "")
        stage     = fx.get("stage", "group")
        venue     = fx.get("venue", fx.get("city", ""))
        kickoff   = fx.get("kickoff_ist", "")

        ko        = format_kickoff(kickoff)
        home_rank = ranks.get(home_id, "—")
        away_rank = ranks.get(away_id, "—")
        home_form = render_form(forms.get(home_id, ""))
        away_form = render_form(forms.get(away_id, ""))

        stage_str = ("Group " + group) if stage == "group" and group else stage.replace("_", " ").title()

        home_flag_div = '<div style="display:flex;align-items:center;justify-content:center;">' + flag_img(home_code, 26) + '</div>'
        away_flag_div = '<div style="display:flex;align-items:center;justify-content:center;">' + flag_img(away_code, 26) + '</div>'

        card = f"""
        <div class="fix-card">
        <div style="display:grid;grid-template-columns:30px 1fr auto 1fr 30px;align-items:center;gap:0.6rem;width:100%;">
            {home_flag_div}
            <div><div style="font-family:'ChampionGothic',sans-serif;font-size:1.5rem;letter-spacing:0.1em;color:#F0F0F0;line-height:1;">{home_code}</div></div>
            <div style="text-align:center;min-width:90px;">
            <div style="font-family:'Inter',sans-serif;font-size:1.5rem;font-weight:800;color:#fff;letter-spacing:0.15em;line-height:1;">{ko}</div>
            </div>
            <div style="text-align:right;"><div style="font-family:'ChampionGothic',sans-serif;font-size:1.5rem;letter-spacing:0.1em;color:#F0F0F0;line-height:1;">{away_code}</div></div>
            {away_flag_div}
        </div>
        <div style="display:grid;grid-template-columns:1fr auto 1fr;align-items:center;margin-top:0.7rem;padding-top:0.6rem;border-top:1px solid #3a3a3a;font-size:0.75rem;font-family:'Inter',sans-serif;">
            <div style="display:flex;align-items:center;gap:0.5rem;"><span style="color:#888;font-weight:600;">{home_rank}</span>{home_form}</div>
            <div style="text-align:center;color:#999;">Match {fx.get("match_id","")} &middot; {stage_str}{(' &middot; ' + venue) if venue else ''}</div>
            <div style="display:flex;align-items:center;gap:0.5rem;justify-content:flex-end;">{away_form}<span style="color:#888;font-weight:600;">{away_rank}</span></div>
        </div>
        </div>
        """

        st.markdown(card, unsafe_allow_html=True)

        # ── Goals ─────────────────────────────────────────────────────────────
        g1, g2 = st.columns(2)
        with g1:
            hg = st.text_input("hg", placeholder="0", key="hg", label_visibility="collapsed")
        with g2:
            ag = st.text_input("ag", placeholder="0", key="ag", label_visibility="collapsed")

    # ── Admin secret ──────────────────────────────────────────────────────────
    secret = st.text_input("", type="password", placeholder="Admin Secret", label_visibility="collapsed")

    # ── Status ────────────────────────────────────────────────────────────────
    if st.session_state.get("admin_status"):
        status = st.session_state["admin_status"]
        cls = "status-ok" if status.startswith("ok:") else "status-err"
        st.markdown(f'<div class="{cls}">{status[3:]}</div>', unsafe_allow_html=True)

    # ── Submit result ─────────────────────────────────────────────────────────
    c1, c2 = st.columns(2)
    with c1:
        if st.button("SUBMIT RESULT", use_container_width=True, key="submit"):
            if secret != ADMIN_SECRET:
                st.session_state["admin_status"] = "err:Invalid admin secret"
                st.rerun()
            elif not fx:
                st.session_state["admin_status"] = "err:No match selected"
                st.rerun()
            else:
                try:
                    update_after_res(supabase, fx["match_id"], int(hg), int(ag))
                    st.session_state["admin_status"] = "ok:Result saved. ELO & standings updated."
                    st.rerun()
                except Exception as e:
                    st.session_state["admin_status"] = "err:" + str(e)
                    st.rerun()

    st.markdown("<div style='margin-top:0.5rem;'></div>", unsafe_allow_html=True)

    # ── Run predictions ───────────────────────────────────────────────────────
    with c2:
        if st.button("RUN PREDICTIONS", use_container_width=True, key="predict"):
            if secret != ADMIN_SECRET:
                st.session_state["admin_status"] = "err:Invalid admin secret"
                st.rerun()
            else:
                with st.spinner("Generating..."):
                    try:
                        @st.cache_resource
                        def get_model():
                            return load_model()
                        model, features = get_model()
                        count = 0
                        for f in fixtures_today(supabase):
                            p = predict_match(model, features, f)
                            pred_updated(supabase, p)
                            count += 1
                        st.session_state["admin_status"] = "ok:Predictions generated for " + str(count) + " match(es)."
                        st.rerun()
                    except Exception as e:
                        st.session_state["admin_status"] = "err:" + str(e)
                        st.rerun()