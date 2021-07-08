#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun May 16 01:32:14 2021

@author: maritush
"""
from google.cloud import firestore
from datetime import datetime, timedelta

import numpy as np
import pandas as pd


import chart_studio.plotly as py
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import plotly.figure_factory as ff
from google.oauth2 import service_account
import plotly.io as pio

import streamlit as st

import json



#cred = credentials.Certificate("frost_forecast_owm.json")
#firebase_admin.initialize_app(cred)
#db = firestore.Client.from_service_account_json("frost_forecast_owm.json")
#db = firestore.client()  # this connects to our Firestore database

key_dict = json.loads(st.secrets["textkey"])
creds = service_account.Credentials.from_service_account_info(key_dict)

# db = firestore.Client.from_service_account_json(json.dumps(key_dict))
db = firestore.Client(credentials=creds, project="custom-temple-312913") #Use Project Id not Project Name
#Pronostico-de-Heladas-Batallas

forcast_collection = db.collection('Forecasts')
timezone_diff= timedelta(hours = 4)

now = datetime.now() - timezone_diff
if now.minute < 3:
    now = now -timedelta(hours=1)
doc = forcast_collection.document(now.strftime('%Y%m%d%H00'))  # specifies the '202103171800' document
values = doc.get().to_dict()

offset = timedelta(hours = 1)
two_days_offset = timedelta(hours = 48) 
before = datetime.now() - two_days_offset -timezone_diff
measured_range = pd.date_range(start= before+offset,periods = 48,freq='h')
forecasted_range = pd.date_range(start= now+offset,periods = 24,freq='h')
measured = pd.DataFrame(values['measured'][::-1],index = pd.to_datetime(measured_range.strftime('%Y%m%d%H00')))
forecasted = pd.DataFrame(values['forecast'],index = pd.to_datetime(forecasted_range.strftime('%Y%m%d%H00')))
forecasted.loc[measured.index[-1]]=measured.iloc[-1]
forecasted= forecasted.sort_index()
st.title('Sistema de pronostico y alerta temprana ante heladas')



# fig = go.Figure()
# fig.add_trace(go.Scatter(x=measured.index, y=measured[0], name= 'Measured Te Amb',showlegend=True))
# fig.add_trace(go.Scatter(x=forecasted.index, y=forecasted[0], name= 'Forecasted Te Amb',showlegend=True))

# fig.update_xaxes(title_text= 'Time')
# fig.update_yaxes(title_text= 'Temperatura [°C]')   
# fig.update_layout(title_text="Pronostico de la temperatura : Batallas")
# st.plotly_chart(fig)


std = np.array([0,0.1538073960085951, 0.182573145216934, 0.2684288896918868,
       0.3564124460799613, 0.40493668007771894, 0.5208442654896113,
       0.48466375049222965, 0.49739921107537455, 0.6086748652457432,
       0.6790776796340291, 0.6646592778762843, 0.6444529749933195,
       0.643997241049695, 0.6586570311345119, 0.6830488941790964,
       0.7202596734098968, 0.7316954520595191, 0.7369931070178055,
       0.7880383802271815, 0.8939606544494744, 1.0266284838943134,
       1.1250693224470059, 1.2478295309199694, 1.3765725260136858])

forecast_load_chart = go.Scatter(x=forecasted.index, y=forecasted[0],
                          mode='lines',              
                           line = dict(color = 'red'),opacity = 0.8,fillcolor='rgba(68, 68, 68, 0.3)',
                           fill='tonexty',showlegend=True,name="Temperatura Pronosticada")

# =============================================================================
# forecasted_load_chart = go.Scatter(x=((self.dates[self.forecast_init+1:actual_date+1+1])),
#                           y=self.forecasted_loads[0,:actual_date-self.forecast_init+1],mode='lines',
#                           line = dict(color = 'red'),opacity = 0.8,fillcolor='rgba(68, 68, 68, 0.3)',
#                           fill='tonexty',showlegend=False)
# 
# =============================================================================
measured_load_chart= go.Scatter(x=measured.index, y=measured[0],
                   name = "Temperatura Observada",line = dict(color = '#636EFA'),opacity = 0.8)

upper_bound_forecast_chart = go.Scatter(name='Intervalo de Confianza',
                                x = forecasted.index,
                                y=forecasted[0]+std,
                                mode='lines',marker=dict(color="#444"),  line=dict(width=0),
                                fillcolor='rgba(68, 68, 68, 0.3)', fill='tonexty')

low_bound_forecast_chart = go.Scatter(x=forecasted.index,
                             y=forecasted[0]-std,
                             marker=dict(color="#444"), line=dict(width=0), 
                             mode='lines',showlegend=False)

# =============================================================================
# upper_bound_forecasted_chart = go.Scatter(x=self.dates[self.forecast_init+1:actual_date+1+1],
#                                  y=(1+self.intervals_h[1,:actual_date-self.forecast_init+1])*self.forecasted_loads[0,:actual_date-self.forecast_init+1],
#                                  mode='lines',marker=dict(color="#444"),
#                                  line=dict(width=0),fillcolor='rgba(68, 68, 68, 0.3)',
#                                  fill='tonexty',showlegend=False)
# 
# low_bound_forecasted_chart = go.Scatter(x=self.dates[self.forecast_init+1:actual_date+1+1],
#                                y=(1-(self.intervals_d[0,:actual_date-self.forecast_init+1]))*self.forecasted_loads[0,:actual_date-self.forecast_init+1],
#                                marker=dict(color="#444"), line=dict(width=0), 
#                                mode='lines',showlegend=False)
# =============================================================================
 
# error_chart = go.Scatter(x=self.dates[self.forecast_init+1:actual_date+1],
#                 y=(self.relative_residuals[0]),
#                 name = "Porcentrual Residual",
#                 xaxis="x",
#                 yaxis="y2")   
#The charts have a specific order to be displayed in the plot (plotly)
#charts =[low_bound_forecast_chart,forecast_load_chart,upper_bound_forecast_chart, measured_load_chart,low_bound_forecasted_chart,forecasted_load_chart,upper_bound_forecasted_chart,error_chart]
charts = [low_bound_forecast_chart,forecast_load_chart,upper_bound_forecast_chart,measured_load_chart]
date_format='%H:%M %d-%b'

layout = dict(title = "Pronostico de la temperatura : Municipio de Batallas", height=600, width=1000,
            xaxis = dict(title='Tiempo [H]',#tickformat = date_format,
                    range=[measured.index[0],forecasted.index[-1]]),
            yaxis = dict(title='Temperatura [°C]'),
            legend=dict(traceorder="reversed"),
            shapes=[dict(type="rect", xref="x", yref="paper",
                         x0=measured.index[-1],y0=0,
                         x1=forecasted.index[-1],
                         y1=1,fillcolor="LightSalmon",opacity=0.3,
                         layer="below",line_width=0)])
fig = go.Figure(data=charts, layout=layout)

f,_=np.where(forecasted.values<=0)

if len(f) == 0:
    pass
elif (len(f)==1):
    

    fig.add_vrect(
        x0=forecasted.index[f[0]], x1=forecasted.index[f[-1]+1],
        fillcolor="LightSalmon", opacity=1,
        layer="below", line_width=0, )
else:
    fig.add_vrect(
        x0=forecasted.index[f[0]], x1=forecasted.index[f[-1]],
        fillcolor="LightSalmon", opacity=1,
        layer="below", line_width=0)
    
fig.add_hline(y=0, line_dash="dot")
    
st.plotly_chart(fig)
