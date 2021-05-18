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


now = datetime.now()
doc = forcast_collection.document(now.strftime('%Y%m%d%H00'))  # specifies the '202103171800' document
values = doc.get().to_dict()

offset = timedelta(hours = 1)
two_days_offset = timedelta(hours = 48) 
before = datetime.now() - two_days_offset 
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
                                y=forecasted[0]+[round((2.4+i)/24,3) for i in range(len(forecasted))],
                                mode='lines',marker=dict(color="#444"),  line=dict(width=0),
                                fillcolor='rgba(68, 68, 68, 0.3)', fill='tonexty')

low_bound_forecast_chart = go.Scatter(x=forecasted.index,
                             y=forecasted[0]-[round((4.8+i)/24,3) for i in range(len(forecasted))],
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
            xaxis = dict(title='Time [H]',tickformat = date_format,
                    range=[measured.index[0],forecasted.index[-1]]),
            yaxis = dict(title='Temperatures [C]'),
            legend=dict(traceorder="reversed"),
            shapes=[dict(type="rect", xref="x", yref="paper",
                         x0=measured.index[-1],y0=0,
                         x1=forecasted.index[-1],
                         y1=1,fillcolor="LightSalmon",opacity=0.5,
                         layer="below",line_width=0)])
st.plotly_chart(dict(data=charts, layout=layout))
