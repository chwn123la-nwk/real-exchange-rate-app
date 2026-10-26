# Real Exchange Rate App

This Streamlit app uses monthly IMF data to calculate and visualize bilateral real exchange rates.

Users can:
- Select Country 1 and Country 2
- Choose a sample period
- View the real exchange rate index
- View the nominal exchange rate
- Display both series using separate axes
- Download the underlying data and calculations as a CSV file

The real exchange rate is calculated as:

RER(t) = S(t) × P1(t) / P2(t)

where S(t) is units of Country 2 currency per one unit of Country 1 currency.

The real exchange rate index is:

Real Index(t) = 100 × RER(t) / RER*

where RER* is the average real exchange rate over the selected sample period.

Data source: International Monetary Fund SDMX API.
