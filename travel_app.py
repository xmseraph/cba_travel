import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="CBA Travel Mileage", layout="wide")
st.title("CBA 2025-26 赛季球队旅行里程（公里）")

df_orig = pd.read_csv("cba_travel_detail_2025_26.csv")
df_opt = pd.read_csv("cba_travel_detail_optimized_2025_26.csv")
df_lb = pd.read_csv("cba_travel_lower_bound.csv", index_col="Team")

df_orig["Schedule"] = "Original"
df_opt["Schedule"] = "Optimized"

teams = sorted(df_orig["Team"].unique())

show_all = st.checkbox("Show all 20 teams", value=True)

if show_all:
    selected = teams
else:
    selected = st.multiselect("Select teams to compare", teams, default=teams[:3])

if selected:
    color_scale = alt.Scale(domain=sorted(selected))

    tab1, tab2, tab3 = st.tabs(["Original", "Optimized", "Comparison"])

    with tab1:
        filtered = df_orig[df_orig["Team"].isin(selected)]
        chart = (
            alt.Chart(filtered)
            .mark_line(point=True)
            .encode(
                x=alt.X("Round:Q", title="Round"),
                y=alt.Y("Km:Q", title="Km"),
                color=alt.Color("Team:N", scale=color_scale, legend=alt.Legend(columns=2)),
                tooltip=["Team", "Round", "Km", "From", "To"],
            )
            .interactive()
            .properties(height=500)
        )
        st.altair_chart(chart, use_container_width=True)

    with tab2:
        filtered = df_opt[df_opt["Team"].isin(selected)]
        chart = (
            alt.Chart(filtered)
            .mark_line(point=True)
            .encode(
                x=alt.X("Round:Q", title="Round"),
                y=alt.Y("Km:Q", title="Km"),
                color=alt.Color("Team:N", scale=color_scale, legend=alt.Legend(columns=2)),
                tooltip=["Team", "Round", "Km", "From", "To"],
            )
            .interactive()
            .properties(height=500)
        )
        st.altair_chart(chart, use_container_width=True)

    with tab3:
        combined = pd.concat([
            df_orig[df_orig["Team"].isin(selected)],
            df_opt[df_opt["Team"].isin(selected)],
        ])
        chart = (
            alt.Chart(combined)
            .mark_line(point=True)
            .encode(
                x=alt.X("Round:Q", title="Round"),
                y=alt.Y("Km:Q", title="Km"),
                color=alt.Color("Team:N", scale=color_scale, legend=alt.Legend(columns=2)),
                strokeDash=alt.StrokeDash("Schedule:N", legend=alt.Legend(title="Schedule")),
                tooltip=["Team", "Schedule", "Round", "Km", "From", "To"],
            )
            .interactive()
            .properties(height=500)
        )
        st.altair_chart(chart, use_container_width=True)

    # Summary table
    st.subheader("赛季总旅行距离（公里）")
    orig_totals = df_orig[df_orig["Team"].isin(selected)].groupby("Team")["Km"].sum()
    opt_totals = df_opt[df_opt["Team"].isin(selected)].groupby("Team")["Km"].sum()
    summary = pd.DataFrame({
        "Original": orig_totals,
        "Optimized": opt_totals,
        "Constraint-Free (km)": df_lb.loc[df_lb.index.isin(selected), "LowerBound"],
    })
    summary["Saved"] = summary["Original"] - summary["Optimized"]
    summary["Saved %"] = (summary["Saved"] / summary["Original"] * 100).round(1).astype(str) + "%"
    summary["vs CF Floor"] = (
        (summary["Optimized"] / summary["Constraint-Free (km)"] * 100).round(0).astype(int).astype(str) + "%"
    )
    st.dataframe(summary, use_container_width=True)
else:
    st.info("Select at least one team.")
