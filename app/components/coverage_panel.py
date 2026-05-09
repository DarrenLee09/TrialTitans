"""Sidebar coverage panel: per-state statute count, verified %, factor coverage (n/total)."""
from __future__ import annotations

import streamlit as st

from db.seed import connect


def _coverage_rows() -> list[dict]:
    with connect() as conn:
        total_factors = conn.execute(
            "SELECT COUNT(*) AS c FROM contributing_factors"
        ).fetchone()["c"] or 0

        rows = [dict(r) for r in conn.execute(
            """
            SELECT
                j.code, j.name,
                (SELECT COUNT(*) FROM statutes s WHERE s.jurisdiction_id = j.id) AS n_statutes,
                (SELECT COUNT(*) FROM statutes s
                  WHERE s.jurisdiction_id = j.id AND s.is_verified = 1) AS n_verified,
                (SELECT COUNT(DISTINCT t.factor_id)
                   FROM statute_factor_tags t
                   JOIN statutes s ON s.id = t.statute_id
                  WHERE s.jurisdiction_id = j.id) AS n_factors
            FROM jurisdictions j
            ORDER BY j.name
            """
        )]
        for r in rows:
            r["total_factors"] = total_factors
        return rows


def render() -> None:
    st.sidebar.markdown("### Coverage")

    rows = _coverage_rows()
    grand_total = sum(r["n_statutes"] for r in rows)
    st.sidebar.metric("Statutes ingested", grand_total)

    if rows and rows[0]["total_factors"]:
        st.sidebar.caption(f"Tracking {rows[0]['total_factors']} contributing factors")
    st.sidebar.divider()

    for r in rows:
        n = r["n_statutes"]
        v_pct = (r["n_verified"] / n) if n else 0
        f_pct = (r["n_factors"] / r["total_factors"]) if r["total_factors"] else 0

        st.sidebar.markdown(f"**{r['code']} — {r['name']}**")
        st.sidebar.caption(
            f"{n} statutes · {r['n_verified']} verified ({v_pct:.0%}) · "
            f"{r['n_factors']}/{r['total_factors']} factors"
        )
        st.sidebar.progress(f_pct, text=f"factor coverage {f_pct:.0%}")
