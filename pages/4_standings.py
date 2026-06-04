import streamlit as st
from collections import defaultdict
from db import get_client, standings_all
from utils import flag_img

supabase = get_client()

st.markdown("""
<style>
.page-title {
    font-family:'ChampionGothic',sans-serif; font-weight:900;
    font-size: 5rem;
    letter-spacing: 0.1em;
    color: #F0F0F0;
    margin-bottom: 0.15rem;
}
.page-sub {
    font-size: 0.9rem; color: #555;
    letter-spacing: 0.12em; text-transform: uppercase;
    margin-bottom: 2rem;
}
.group-card {
    background: rgba(10,10,10,0.55);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-radius: 10px;
    border: 1px solid #242424;
    padding: 1rem 1.2rem;
    margin-bottom: 1rem;
}
.group-title {
    font-family: 'ChampionGothic', 'Inter', sans-serif;
    font-size: 1.3rem;
    letter-spacing: 0.1em;
    color: #F0F0F0;
    margin-bottom: 0.75rem;
    border-bottom: 1px solid #3a3a3a;
    padding-bottom: 0.5rem;
}
.stand-header {
    display: grid;
    grid-template-columns: 2fr 1fr 1fr 1fr 1fr 1fr 1fr;
    font-size: 0.65rem;
    color: #444;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    padding: 0 0.25rem;
    margin-bottom: 0.4rem;
}
.stand-row {
    display: grid;
    grid-template-columns: 2fr 1fr 1fr 1fr 1fr 1fr 1fr;
    align-items: center;
    padding: 0.4rem 0.25rem;
    border-radius: 6px;
    font-size: 0.82rem;
}
.stand-row:hover { background: rgba(255,255,255,0.03); }
.stand-row.qualify { border-left: 2px solid #00C853; padding-left: 0.4rem; }
.team-cell {
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

/* ── Mobile: stack groups full width ── */
@media (max-width: 767px) {
    [data-testid="stColumns"] {
        flex-direction: column !important;
    }
    [data-testid="stColumn"] {
        width: 100% !important;
        flex: 1 1 100% !important;
        min-width: 100% !important;
    }
    .stand-header, .stand-row {
        grid-template-columns: 2fr 1fr 1fr 1fr 1fr 1fr 1fr;
        font-size: 0.6rem;
    }
    .group-card {
        padding: 0.75rem 0.85rem;
    }
}
</style>
""", unsafe_allow_html=True)

st.markdown(
    '<div class="page-title">STANDINGS</div>',
    unsafe_allow_html=True
)

all_rows = standings_all(supabase)

if not all_rows:
    st.info("Standings not available yet.")
    st.stop()

by_group = defaultdict(list)
for row in all_rows:
    by_group[row["group_name"]].append(row)

groups_sorted = sorted(by_group.keys())

for i in range(0, len(groups_sorted), 3):
    cols = st.columns(3)
    for j, grp in enumerate(groups_sorted[i:i+3]):
        rows = sorted(by_group[grp], key=lambda x: (-x["points"], -x.get("gd", 0), -x.get("gf", 0)))

        with cols[j]:
            header_html = (
                '<div class="group-card">'
                '<div class="group-title">GROUP ' + grp + '</div>'
                '<div class="stand-header">'
                '<div>Team</div>'
                '<div style="font-family:\'Inter\',sans-serif;text-align:center;">P</div>'
                '<div style="font-family:\'Inter\',sans-serif;text-align:center;">W</div>'
                '<div style="font-family:\'Inter\',sans-serif;text-align:center;">D</div>'
                '<div style="font-family:\'Inter\',sans-serif;text-align:center;">L</div>'
                '<div style="font-family:\'Inter\',sans-serif;text-align:center;">GD</div>'
                '<div style="font-family:\'Inter\',sans-serif;text-align:center;">Pts</div>'
                '</div>'
            )

            rows_html = ""
            for idx, row in enumerate(rows):
                team = row.get("team", {})
                code = team.get("team_code", "???")
                qualify_cls = "stand-row"
                gd = row.get("gd", 0)
                gd_str = ("+" if gd > 0 else "") + str(gd)

                rows_html += (
                    '<div class="' + qualify_cls + '">'

                    '<div class="team-cell">'
                    + flag_img(code, 20) +
                    '<span style="font-family:\'ChampionGothic\',sans-serif;'
                    'font-size:0.95rem;letter-spacing:0.08em;color:#F0F0F0;">' + code + '</span>'
                    '</div>'

                    '<div style="font-family:\'Inter\',sans-serif;text-align:center;color:#888;">' + str(row.get("played", 0)) + '</div>'
                    '<div style="font-family:\'Inter\',sans-serif;text-align:center;color:#888;">' + str(row.get("won", 0)) + '</div>'
                    '<div style="font-family:\'Inter\',sans-serif;text-align:center;color:#888;">' + str(row.get("drawn", 0)) + '</div>'
                    '<div style="font-family:\'Inter\',sans-serif;text-align:center;color:#888;">' + str(row.get("lost", 0)) + '</div>'
                    '<div style="font-family:\'Inter\',sans-serif;text-align:center;color:#888;">' + gd_str + '</div>'
                    '<div style="font-family:\'Inter\',sans-serif;text-align:center;font-family:\'ChampionGothic\',sans-serif;'
                    'font-size:1rem;color:#f0f0f0f;">' + str(row.get("points", 0)) + '</div>'

                    '</div>'
                )

            st.markdown(header_html + rows_html + '</div>', unsafe_allow_html=True)
