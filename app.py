import geopandas as gp
import pandas as pd
import plotly.express as px
import streamlit as st

# --- INITIALIZE DATA ---

df = pd.read_csv(
    "data/liikenneonnettomuudet_Helsingissa.csv", 
    sep=";"
)

gdf = gp.GeoDataFrame(
    df,
    geometry=gp.points_from_xy(
        df.ita_etrs, df.pohj_etrs
    ),
    crs="EPSG:3879"
)

gdf = gdf.to_crs(epsg=4326)

df["lon"] = gdf.geometry.x
df["lat"] = gdf.geometry.y

geojson = gdf.__geo_interface__

# For the area plot
df_counts = (
    df
    .groupby(["VV", "LAJI"])
    .size()
    .reset_index(name="count")
)

df_counts = df_counts.rename({"VV": "Year", "LAJI": "Type of accident"}, axis=1)
category_map = {
    "JK": "pedestrian",
    "MA": "motor vehicle",
    "MP": "motorcycle",
    "PP": "bicycle"
}

df_counts["Type of accident"] = df_counts["Type of accident"].map(category_map)


# --- PLOTLY ---

fig = px.choropleth_map(
    gdf,
    geojson=geojson,
    locations=gdf.index,
    map_style="basic",
    zoom=10,
    center={"lat": df["lat"].mean(), "lon": df["lon"].mean()},
    opacity=0.8
)

fig.add_trace(
    px.density_map(
        df,
        lat="lat",
        lon="lon",
        z="VAKAV_A",  # intensity
        radius=15,
        opacity=0.5,
        color_continuous_scale="Blues",
    ).data[0]
)

fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

fig2 = px.area(
    df_counts,
    x="Year",
    y="count",
    color="Type of accident",
)

# --- STREAMLIT ---

st.title("Helsinki Traffic Safety Analysis")

st.plotly_chart(fig, width='stretch', theme=None)

st.plotly_chart(fig2, width='stretch', theme=None)


