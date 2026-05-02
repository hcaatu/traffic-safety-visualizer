import geopandas as gp
import pandas as pd
import plotly.express as px
import streamlit as st

# --- INITIALIZE DATA ---

df = pd.read_csv(
    "data/liikenneonnettomuudet_Helsingissa.csv", 
    sep=";"
)

def filter_by_accident_type(input_df: pd.DataFrame, filter: str) -> pd.DataFrame:
    if filter == "none":
        return input_df
    filtered_df = input_df.copy()
    print(filtered_df.shape)
    filtered_df = filtered_df[filtered_df["Type of accident"] == filter]
    print(filtered_df.shape)
    return filtered_df

def get_gdf(df):
    gdf = gp.GeoDataFrame(
        df,
        geometry=gp.points_from_xy(
            df.ita_etrs, df.pohj_etrs
        ),
        crs="EPSG:3879"
    )

    gdf = gdf.to_crs(epsg=4326)
    return gdf

def get_geojson(gdf):
    df["lon"] = gdf.geometry.x
    df["lat"] = gdf.geometry.y

    geojson = gdf.__geo_interface__
    return geojson

# For the area plot
df_counts = (
    df
    .groupby(["VV", "LAJI"])
    .size()
    .reset_index(name="count")
)

def rename_columns(input_df):
    df = input_df.copy()
    df = df.rename({
        "VV": "Year", 
        "LAJI": "Type of accident",
        "VAKAV_A": "Severity"
    }, axis=1)

    category_map = {
        "JK": "pedestrian",
        "MA": "motor vehicle",
        "MP": "motorcycle",
        "PP": "bicycle"
    }

    df["Type of accident"] = df["Type of accident"].map(category_map)

    return df

df = rename_columns(df)
df_counts = rename_columns(df_counts)


# --- PLOTLY ---

def plot_heatmap(gdf, geojson):
    print(f"plotted gdf shape {gdf.shape}")
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
            z="Severity",  # intensity
            radius=15,
            opacity=0.5,
            color_continuous_scale="Blues",
        ).data[0]
    )

    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

    return fig

def plot_area(df):
    fig2 = px.area(
        df,
        x="Year",
        y="count",
        color="Type of accident",
    )
    return fig2

# --- STREAMLIT ---

st.title("Helsinki Traffic Safety Analysis")

option = st.selectbox(
    "Filter by accident type",
    ("none", "motor vehicle", "motorcycle", "bicycle", "pedestrian")
)

df = filter_by_accident_type(df, option)
gdf = get_gdf(df)
geojson = get_geojson(gdf)

st.plotly_chart(plot_heatmap(gdf, geojson), width='stretch', theme=None)

st.plotly_chart(plot_area(df_counts), width='stretch', theme=None)


