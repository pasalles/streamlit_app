from google.cloud import bigquery
from google.oauth2 import service_account
import pandas as pd
import plotly.express as px
import streamlit as st


# Bigquery connection
credentials = service_account.Credentials.from_service_account_file(
'service-account-file.json')

project_id = 'geometric-gamma-370017'
client = bigquery.Client(credentials= credentials,project=project_id)

# Time intervals for the SQL query

time_intervals = ['1 day', '1 week', '1 month']
time_interval = '1 day'


selected_time = st.selectbox("Time interval:",
options=time_intervals,
index=time_intervals.index(time_interval)
)

if selected_time == '1 day':
    time_interval = '1 day'
elif selected_time == '1 week':
    time_interval = '7 day'
else:
    time_interval = '30 day'

# SQL Query (the "f" allows to insert parameters)
query = f"""WITH stocks_with_recent_price AS (
  SELECT 
    stock_code, 
    MAX(DATE(time_stamp)) AS recent_date
  FROM `geometric-gamma-370017.webscraper_listings.stocks_data`
  GROUP BY stock_code
)
SELECT 
  s1.stock_code,
  s1.company,
  s1.sector,
  s1.industry,
  s1.market_cap,
  s1.price AS recent_price,
  s2.price AS previous_price, 
  s1.price - s2.price AS price_difference
FROM `geometric-gamma-370017.webscraper_listings.stocks_data` s1
JOIN stocks_with_recent_price swrp
  ON s1.stock_code = swrp.stock_code
  AND DATE(s1.time_stamp) = swrp.recent_date
JOIN `geometric-gamma-370017.webscraper_listings.stocks_data` s2
  ON s1.stock_code = s2.stock_code
  AND DATE(s2.time_stamp) = DATE_SUB(DATE(s1.time_stamp), INTERVAL {time_interval})
"""

# Run the query
query_job = client.query(query)
df = query_job.to_dataframe()

# Create the Treemap chart
fig = px.treemap(df, path=['sector', 'industry', 'stock_code'], values='market_cap',
                  color='price_difference', hover_data=['price_difference'], 
                  color_continuous_scale=[(0, "#f63538"), (0.5, "#414554"), (1, "#30cc5a")],
                  color_continuous_midpoint=0, range_color=[-3,3])

fig.data[0].customdata = fig.data[0].marker.colors
fig.data[0].texttemplate = "<b>%{label}</b><br>Market Cap: %{value:.0f} B<br>price_difference: %{customdata:.2f}%<br>"
fig.update_traces(hovertemplate='%{label}<br>price_difference=%{customdata:.2f}%')
fig.update_traces(marker=dict(line=dict(width=1, color='#262931')))
fig.update_layout({
    'plot_bgcolor': 'rgba(0,0,0,0)',
    'paper_bgcolor': 'rgba(0,0,0,0)'
})
fig.update_layout(margin = dict(t=10, l=10, r=10, b=10), autosize=True, width=1000)

st.plotly_chart(fig, use_container_width=True)
