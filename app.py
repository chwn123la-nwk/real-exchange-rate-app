import io

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

st.set_page_config(
    page_title="Real Exchange Rate App",
    page_icon="🌍",
    layout="wide",
)

# ------------------------------------------------------------
# Country list
# IMF uses ISO3 country codes. G163 represents the Euro area.
# ------------------------------------------------------------

COUNTRIES = {
    "United States": "USA",
    "United Kingdom": "GBR",
    "Euro Area": "G163",
    "Albania": "ALB",
    "Algeria": "DZA",
    "Angola": "AGO",
    "Argentina": "ARG",
    "Armenia": "ARM",
    "Australia": "AUS",
    "Austria": "AUT",
    "Azerbaijan": "AZE",
    "Bahamas": "BHS",
    "Bahrain": "BHR",
    "Bangladesh": "BGD",
    "Barbados": "BRB",
    "Belarus": "BLR",
    "Belgium": "BEL",
    "Belize": "BLZ",
    "Benin": "BEN",
    "Bhutan": "BTN",
    "Bolivia": "BOL",
    "Bosnia and Herzegovina": "BIH",
    "Botswana": "BWA",
    "Brazil": "BRA",
    "Brunei Darussalam": "BRN",
    "Bulgaria": "BGR",
    "Burkina Faso": "BFA",
    "Burundi": "BDI",
    "Cabo Verde": "CPV",
    "Cambodia": "KHM",
    "Cameroon": "CMR",
    "Canada": "CAN",
    "Central African Republic": "CAF",
    "Chad": "TCD",
    "Chile": "CHL",
    "China": "CHN",
    "Colombia": "COL",
    "Comoros": "COM",
    "Costa Rica": "CRI",
    "Croatia": "HRV",
    "Cyprus": "CYP",
    "Czech Republic": "CZE",
    "Denmark": "DNK",
    "Dominican Republic": "DOM",
    "Ecuador": "ECU",
    "Egypt": "EGY",
    "El Salvador": "SLV",
    "Estonia": "EST",
    "Eswatini": "SWZ",
    "Ethiopia": "ETH",
    "Fiji": "FJI",
    "Finland": "FIN",
    "France": "FRA",
    "Gabon": "GAB",
    "Georgia": "GEO",
    "Germany": "DEU",
    "Ghana": "GHA",
    "Greece": "GRC",
    "Guatemala": "GTM",
    "Guinea": "GIN",
    "Guyana": "GUY",
    "Haiti": "HTI",
    "Honduras": "HND",
    "Hong Kong SAR": "HKG",
    "Hungary": "HUN",
    "Iceland": "ISL",
    "India": "IND",
    "Indonesia": "IDN",
    "Iran": "IRN",
    "Iraq": "IRQ",
    "Ireland": "IRL",
    "Israel": "ISR",
    "Italy": "ITA",
    "Jamaica": "JAM",
    "Japan": "JPN",
    "Jordan": "JOR",
    "Kazakhstan": "KAZ",
    "Kenya": "KEN",
    "Korea": "KOR",
    "Kuwait": "KWT",
    "Kyrgyz Republic": "KGZ",
    "Lao P.D.R.": "LAO",
    "Latvia": "LVA",
    "Lebanon": "LBN",
    "Lesotho": "LSO",
    "Liberia": "LBR",
    "Lithuania": "LTU",
    "Luxembourg": "LUX",
    "Madagascar": "MDG",
    "Malawi": "MWI",
    "Malaysia": "MYS",
    "Maldives": "MDV",
    "Mali": "MLI",
    "Malta": "MLT",
    "Mauritania": "MRT",
    "Mauritius": "MUS",
    "Mexico": "MEX",
    "Moldova": "MDA",
    "Mongolia": "MNG",
    "Montenegro": "MNE",
    "Morocco": "MAR",
    "Mozambique": "MOZ",
    "Myanmar": "MMR",
    "Namibia": "NAM",
    "Nepal": "NPL",
    "Netherlands": "NLD",
    "New Zealand": "NZL",
    "Nicaragua": "NIC",
    "Niger": "NER",
    "Nigeria": "NGA",
    "North Macedonia": "MKD",
    "Norway": "NOR",
    "Oman": "OMN",
    "Pakistan": "PAK",
    "Panama": "PAN",
    "Papua New Guinea": "PNG",
    "Paraguay": "PRY",
    "Peru": "PER",
    "Philippines": "PHL",
    "Poland": "POL",
    "Portugal": "PRT",
    "Qatar": "QAT",
    "Romania": "ROU",
    "Russia": "RUS",
    "Rwanda": "RWA",
    "Saudi Arabia": "SAU",
    "Senegal": "SEN",
    "Serbia": "SRB",
    "Seychelles": "SYC",
    "Sierra Leone": "SLE",
    "Singapore": "SGP",
    "Slovak Republic": "SVK",
    "Slovenia": "SVN",
    "South Africa": "ZAF",
    "Spain": "ESP",
    "Sri Lanka": "LKA",
    "Sudan": "SDN",
    "Suriname": "SUR",
    "Sweden": "SWE",
    "Switzerland": "CHE",
    "Taiwan Province of China": "TWN",
    "Tajikistan": "TJK",
    "Tanzania": "TZA",
    "Thailand": "THA",
    "Togo": "TGO",
    "Trinidad and Tobago": "TTO",
    "Tunisia": "TUN",
    "Türkiye": "TUR",
    "Uganda": "UGA",
    "Ukraine": "UKR",
    "United Arab Emirates": "ARE",
    "Uruguay": "URY",
    "Uzbekistan": "UZB",
    "Venezuela": "VEN",
    "Vietnam": "VNM",
    "Zambia": "ZMB",
    "Zimbabwe": "ZWE",
}

IMF_BASE = "https://api.imf.org/external/sdmx/3.0/data/dataflow"


# ------------------------------------------------------------
# IMF API functions
# ------------------------------------------------------------

def parse_imf_csv(response):
    response.raise_for_status()

    if not response.text.strip():
        return pd.DataFrame()

    df = pd.read_csv(io.StringIO(response.text))

    if "TIME_PERIOD" not in df.columns or "OBS_VALUE" not in df.columns:
        return pd.DataFrame()

    result = df[["TIME_PERIOD", "OBS_VALUE"]].copy()

    result["Date"] = pd.to_datetime(
        result["TIME_PERIOD"]
        .astype(str)
        .str.replace("-M", "-", regex=False),
        errors="coerce",
    )

    result["Value"] = pd.to_numeric(result["OBS_VALUE"], errors="coerce")

    return (
        result[["Date", "Value"]]
        .dropna()
        .drop_duplicates(subset=["Date"])
        .sort_values("Date")
        .reset_index(drop=True)
    )


@st.cache_data(ttl=3600)
def fetch_cpi(country_code):
    key = f"{country_code}.CPI._T.IX.M"

    url = (
        f"{IMF_BASE}/IMF.STA/CPI/~/{key}"
        "?c[TIME_PERIOD]=ge:1976-M01"
    )

    response = requests.get(
        url,
        headers={"Accept": "text/csv"},
        timeout=30,
    )

    return parse_imf_csv(response)


@st.cache_data(ttl=3600)
def fetch_fx(country_code):
    if country_code == "USA":
        dates = pd.date_range(
            start="1976-01-01",
            end=pd.Timestamp.today().replace(day=1),
            freq="MS",
        )

        return pd.DataFrame(
            {
                "Date": dates,
                "Value": 1.0,
            }
        )

    key = f"{country_code}.XDC_USD.PA_RT.M"

    url = (
        f"{IMF_BASE}/IMF.STA/ER/~/{key}"
        "?c[TIME_PERIOD]=ge:1976-M01"
    )

    response = requests.get(
        url,
        headers={"Accept": "text/csv"},
        timeout=30,
    )

    return parse_imf_csv(response)


def build_dataset(country1_code, country2_code):
    cpi1 = fetch_cpi(country1_code).rename(columns={"Value": "P1"})
    cpi2 = fetch_cpi(country2_code).rename(columns={"Value": "P2"})

    fx1 = fetch_fx(country1_code).rename(columns={"Value": "FX1_per_USD"})
    fx2 = fetch_fx(country2_code).rename(columns={"Value": "FX2_per_USD"})

    data = cpi1.merge(cpi2, on="Date", how="inner")
    data = data.merge(fx1, on="Date", how="inner")
    data = data.merge(fx2, on="Date", how="inner")

    # IMF exchange rates are local currency units per USD.
    # Required S(t) is Country 2 currency per one unit of Country 1 currency.
    # Therefore:
    # S(t) = FX2 / FX1

    data["S"] = data["FX2_per_USD"] / data["FX1_per_USD"]

    # Real exchange rate:
    # RER(t) = S(t) × P1(t) / P2(t)

    data["RER"] = data["S"] * data["P1"] / data["P2"]

    data = data.replace([float("inf"), float("-inf")], pd.NA)
    data = data.dropna(subset=["P1", "P2", "S", "RER"])

    return data.sort_values("Date").reset_index(drop=True)


# ------------------------------------------------------------
# App interface
# ------------------------------------------------------------

st.title("Real Exchange Rate App")

st.write(
    "This app uses monthly IMF consumer price index and exchange-rate data "
    "to calculate bilateral real exchange rates."
)

country_names = list(COUNTRIES.keys())

col1, col2 = st.columns(2)

with col1:
    country1 = st.selectbox(
        "Country 1",
        country_names,
        index=country_names.index("United Kingdom"),
    )

with col2:
    country2 = st.selectbox(
        "Country 2",
        country_names,
        index=country_names.index("United States"),
    )

if country1 == country2:
    st.warning("Please select two different countries.")
    st.stop()

code1 = COUNTRIES[country1]
code2 = COUNTRIES[country2]

st.caption(
    f"S(t) is defined as units of {country2} currency per one unit "
    f"of {country1} currency."
)

try:
    with st.spinner("Downloading IMF data..."):
        full_data = build_dataset(code1, code2)

except requests.RequestException as error:
    st.error(
        "The IMF data download failed. The IMF API may be temporarily unavailable."
    )
    st.code(str(error))
    st.stop()

except Exception as error:
    st.error("The data could not be processed.")
    st.code(str(error))
    st.stop()

if full_data.empty:
    st.error(
        "No common monthly CPI and exchange-rate observations are available "
        "for this country pair."
    )
    st.stop()


# ------------------------------------------------------------
# Date selection
# ------------------------------------------------------------

min_date = full_data["Date"].min().date()
max_date = full_data["Date"].max().date()

st.subheader("Sample period")

date_col1, date_col2 = st.columns(2)

with date_col1:
    start_date = st.date_input(
        "Start month",
        value=min_date,
        min_value=min_date,
        max_value=max_date,
    )

with date_col2:
    end_date = st.date_input(
        "End month",
        value=max_date,
        min_value=min_date,
        max_value=max_date,
    )

start_month = pd.Timestamp(start_date).replace(day=1)
end_month = pd.Timestamp(end_date).replace(day=1)

if start_month > end_month:
    st.error("The start month must be before the end month.")
    st.stop()

sample = full_data[
    (full_data["Date"] >= start_month)
    & (full_data["Date"] <= end_month)
].copy()

if sample.empty:
    st.error("There are no valid observations in the selected period.")
    st.stop()


# ------------------------------------------------------------
# RER benchmark and real index
# ------------------------------------------------------------

rer_star = sample["RER"].mean()

sample["RER_star"] = rer_star
sample["Real_Index"] = 100 * sample["RER"] / rer_star

st.metric("Average RER (RER*)", f"{rer_star:.4f}")
st.metric("Average Real Index", f"{sample['Real_Index'].mean():.2f}")

st.caption(
    "RER* is recalculated using all valid observations in the selected "
    "sample period. Therefore, the Real Index averages 100."
)


# ------------------------------------------------------------
# Chart selection
# ------------------------------------------------------------

view = st.radio(
    "Choose chart",
    ["Real", "Nominal", "Both"],
    horizontal=True,
)

fig = go.Figure()

if view == "Real":
    fig.add_trace(
        go.Scatter(
            x=sample["Date"],
            y=sample["Real_Index"],
            mode="lines",
            name="Real Index",
        )
    )

    fig.update_layout(
        yaxis_title="Real Exchange Rate Index (RER* = 100)",
    )

elif view == "Nominal":
    fig.add_trace(
        go.Scatter(
            x=sample["Date"],
            y=sample["S"],
            mode="lines",
            name="Nominal Exchange Rate",
        )
    )

    fig.update_layout(
        yaxis_title=f"{country2} currency per {country1} currency",
    )

else:
    fig.add_trace(
        go.Scatter(
            x=sample["Date"],
            y=sample["Real_Index"],
            mode="lines",
            name="Real Index",
            yaxis="y",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=sample["Date"],
            y=sample["S"],
            mode="lines",
            name="Nominal Exchange Rate",
            yaxis="y2",
        )
    )

    fig.update_layout(
        yaxis=dict(
            title="Real Exchange Rate Index",
        ),
        yaxis2=dict(
            title=f"Nominal S(t): {country2} per {country1}",
            overlaying="y",
            side="right",
        ),
        legend=dict(
            x=0.76,
            y=0.98,
            xanchor="left",
            yanchor="top",
        ),
        margin=dict(
            r=180,
        ),
    )

fig.update_layout(
    title=f"{country1} vs. {country2}",
    xaxis_title="Date",
    hovermode="x unified",
    legend_title="Series",
)

st.plotly_chart(fig, use_container_width=True)


# ------------------------------------------------------------
# Data table
# ------------------------------------------------------------

st.subheader("Selected sample data")

display_data = sample[
    [
        "Date",
        "P1",
        "P2",
        "FX1_per_USD",
        "FX2_per_USD",
        "S",
        "RER",
        "RER_star",
        "Real_Index",
    ]
].copy()

display_data["Date"] = display_data["Date"].dt.strftime("%Y-%m")

display_data = display_data.rename(
    columns={
        "P1": f"CPI_{code1}",
        "P2": f"CPI_{code2}",
        "FX1_per_USD": f"{code1}_per_USD",
        "FX2_per_USD": f"{code2}_per_USD",
        "S": "Nominal_S",
        "RER": "RER",
        "RER_star": "RER_star",
        "Real_Index": "Real_Index",
    }
)

st.dataframe(display_data, use_container_width=True)


# ------------------------------------------------------------
# CSV download
# ------------------------------------------------------------

csv = display_data.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download CSV",
    data=csv,
    file_name=f"real_exchange_rate_{code1}_{code2}.csv",
    mime="text/csv",
)


# ------------------------------------------------------------
# Methodology
# ------------------------------------------------------------

with st.expander("Methodology"):
    st.markdown(
        f"""
**Nominal exchange rate**

S(t) is defined as units of {country2} currency per one unit of
{country1} currency.

The IMF reports exchange rates as local-currency units per U.S. dollar.
Therefore:

S(t) = FX2(t) / FX1(t)

where FX1 is Country 1 currency per USD and FX2 is Country 2 currency
per USD.

**Real exchange rate**

RER(t) = S(t) × P1(t) / P2(t)

**Benchmark**

RER* = average RER(t) over the selected valid sample.

**Real Index**

Real Index(t) = 100 × RER(t) / RER*
"""
    )

st.caption(
    "Source: International Monetary Fund (IMF) SDMX API. "
    "Data availability varies across countries and time."
)
