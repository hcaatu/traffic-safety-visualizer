import geopandas as gp
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from streamlit_plotly_events import plotly_events

# --- INITIALIZE DATA ---

df = pd.read_csv(
    "data/liikenneonnettomuudet_Helsingissa.csv", 
    sep=";"
)

def filter_by_accident_type(input_df: pd.DataFrame, filter: str) -> pd.DataFrame:
    if filter == "None":
        return input_df
    filtered_df = input_df.copy()
    filtered_df = filtered_df[filtered_df["Type of accident"] == filter]
    return filtered_df

def filter_by_year_range(input_df: pd.DataFrame, start_year: int, end_year: int) -> pd.DataFrame:
    df = input_df.copy()
    df = df[df["Year"].between(start_year, end_year)]
    return df

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
        "JK": "Pedestrian",
        "MA": "Motor vehicle",
        "MP": "Motorcycle",
        "PP": "Bicycle"
    }

    df["Type of accident"] = df["Type of accident"].map(category_map)

    return df

df = rename_columns(df)
df_counts = rename_columns(df_counts)


# --- PLOTLY ---

def plot_heatmap(gdf, geojson, zoom, center, radius, scatter=False):
    if scatter:
        # Build density map first as the base figure
        fig = px.density_map(
            df,
            lat="lat",
            lon="lon",
            #z="Severity",
            zoom=zoom,
            center=center,
            radius=15,
            opacity=0.7,
            color_continuous_scale="sunsetdark",
        )
    
        fig.add_trace(
            px.scatter_map(
                df,
                lat="lat",
                lon="lon",
                color="Severity",
                hover_data=["Severity", "Year", "Type of accident"]
            ).data[0]
        )
        
    else:
        fig = px.density_map(
            df,
            lat="lat",
            lon="lon",
            z="Severity",
            zoom=zoom,
            center=center,
            radius=15,
            opacity=1,
            color_continuous_scale="sunsetdark",
        )

    fig.update_layout(
        uirevision="constant",
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        coloraxis_colorbar=dict(
            title="Risk Factor",
            tickvals=[1, 2, 3],
            ticktext=["Low", "Medium", "High"],
            yanchor="middle", y=0.5, # Vertical position
            thickness=20, # Thickness of the bar
        )
    )

    return fig

def plot_area(df):
    fig2 = px.area(
        df,
        x="Year",
        y="count",
        color="Type of accident",
        title="Accident trends per type"
    )

    fig2.update_layout(uirevision="constant")
    return fig2

# --- STREAMLIT ---

st.title("Helsinki Traffic Safety Visualizer")

option = st.selectbox(
    "Filter by accident type",
    ("None", "Motor vehicle", "Motorcycle", "Bicycle", "Pedestrian")
)

start_year, end_year = st.select_slider("Filter by year", options=range(2000, 2024+1), value=(2000, 2024))

scatter = st.checkbox(
    "Show individual data points"
)

df = filter_by_accident_type(df, option)
df = filter_by_year_range(df, start_year, end_year)
gdf = get_gdf(df)
geojson = get_geojson(gdf)

BASE_ZOOM = 10
BASE_RADIUS = 15

if "zoom_level" not in st.session_state:
    st.session_state.zoom_level = BASE_ZOOM

# Init defaults
if "map_zoom" not in st.session_state:
    st.session_state.map_zoom = 12
if "map_center" not in st.session_state:
    st.session_state.map_center = {"lat": df["lat"].mean(), "lon": df["lon"].mean()}
if "zoom_level" not in st.session_state:
    st.session_state.zoom_level = BASE_ZOOM

# Calculate radius from zoom
def zoom_to_radius(zoom, base_zoom=BASE_ZOOM, base_radius=BASE_RADIUS):
    radius = base_radius * (2 ** ((zoom - base_zoom) / 2))
    return max(5, min(radius, 100))

current_radius = zoom_to_radius(st.session_state.zoom_level)

fig = plot_heatmap(gdf, geojson, st.session_state.map_zoom, st.session_state.map_center, current_radius, scatter)

st.plotly_chart(fig, width='stretch', theme=None)



with st.expander("ℹ️ More info"):
    st.markdown("""The Risk Factor is based on the severity of the accidents in that area. Hovering over individual data points shows additional information. Accident type reflects the weakest party involved.  
    Severity of accidents is categorized into three groups:""")
    st.table(pd.DataFrame({
        "Property damage",
        "Injury",
        "Fatality",
    }, index=[1, 2, 3]),
    hide_header=True,
    border="horizontal"
    )

with st.expander("📊 Data Source"):
    st.markdown("""
        Accident data from 2000-2024.
        Source: [Traffic Accidents in Helsinki](https://hri.fi/data/en_GB/dataset/liikenneonnettomuudet-helsingissa). 
        The maintainer of the dataset is Helsingin kaupunkiympäristön toimiala / Liikenne- ja katusuunnittelu. 
        The dataset has been downloaded from [Helsinki Region Infoshare](https://hri.fi/) service on 14.04.2026 under the license [Creative Commons Attribution 4.0](https://creativecommons.org/licenses/by/4.0/). 
        """)

st.plotly_chart(plot_area(df_counts), width='stretch', theme=None)

st.markdown("Area plot illustrating the trend of traffic accidents in Helsinki from 2000 to 2025. Toggle the categories on or off from the sidebar")

