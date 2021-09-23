#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun May 16 01:32:14 2021

@author: maritush
"""
from google.cloud import firestore
from datetime import datetime, timedelta, time,date

import numpy as np
import pandas as pd


import chart_studio.plotly as py
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import plotly.figure_factory as ff
from google.oauth2 import service_account
import plotly.io as pio
from PIL import Image
import streamlit as st

import json


def make_forecast_plot(measured,forecasted):
    
    std = np.array([0,0.1538073960085951, 0.182573145216934, 0.2684288896918868,
       0.3564124460799613, 0.40493668007771894, 0.5208442654896113,
       0.48466375049222965, 0.49739921107537455, 0.6086748652457432,
       0.6790776796340291, 0.6646592778762843, 0.6444529749933195,
       0.643997241049695, 0.6586570311345119, 0.6830488941790964,
       0.7202596734098968, 0.7316954520595191, 0.7369931070178055,
       0.7880383802271815, 0.8939606544494744, 1.0266284838943134,
       1.1250693224470059, 1.2478295309199694, 1.3765725260136858])
    std = std+0.1
    
    # =============================================================================
    # Create Forecast Fig
    # =============================================================================
    
    forecast_load_chart = go.Scatter(x=forecasted.index, y=forecasted[0],
                              mode='lines',              
                               line = dict(color = 'red'),opacity = 0.8,fillcolor='rgba(68, 68, 68, 0.3)',
                               fill='tonexty',showlegend=True,name="Temperatura Pronosticada")
    
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
    
    charts = [low_bound_forecast_chart,forecast_load_chart,upper_bound_forecast_chart,measured_load_chart]
    date_format='%H:%M \n%d-%b-%y'
    
    layout = dict( height=600, width=1000,
                xaxis = dict(title='Tiempo [H]',tickformat = date_format,
                        range=[measured.index[0],forecasted.index[-1]]),#,dtick=4*60*60*1000
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
        new_status = '<p style="font-family:sans-serif; color:Black; font-size: 24px;">Ningún evento de helada ha sido pronosticado dentro de las próximas 24 Horas</p>'
    elif (len(f)==1):   
        st.header('Evento de helada pronosticado dentro de las próximas 24 Horas')
        fig.add_vrect(
            x0=forecasted.index[f[0]], x1=forecasted.index[f[-1]+1],
            fillcolor="LightSalmon", opacity=1,
            layer="below", line_width=0, )
        new_status = '<p style="font-family:sans-serif; color:Red; font-size: 24px;">Evento de helada pronosticado dentro de las próximas 24 Horas</p>'
    else:
        fig.add_vrect(
            x0=forecasted.index[f[0]], x1=forecasted.index[f[-1]],
            fillcolor="LightSalmon", opacity=1,
            layer="below", line_width=0)
        new_status = '<p style="font-family:sans-serif; color:Red; font-size: 24px;">Evento de helada pronosticado dentro de las próximas 24 Horas/p>'
    
    
    fig.add_hline(y=0, line_dash="dot")
    
    
    fig.update_layout(legend=dict(
        orientation="h",
        yanchor="bottom", y=1.02,
        xanchor="right",  x=1))
    return fig, new_status
    
@st.cache(suppress_st_warning=True)
def load_images():
    image = Image.open('images/logo_ucb.png')
    image2 = Image.open('images/frost_in_road_view.jpg')
    image3 = Image.open('images/Batallas_view.jpg')
    image4 = Image.open('images/Torre_2.JPG')
    image5 = Image.open('images/Paisaje2.jpeg')
    image6 = Image.open('images/imt_logo.jpg')
    return image,image2,image3,image4,image5,image6



# db = firestore.Client.from_service_account_json("frost_forecast_owm.json")

key_dict = json.loads(st.secrets["textkey"])
creds = service_account.Credentials.from_service_account_info(key_dict)
db = firestore.Client(credentials=creds, project="custom-temple-312913")

st.set_page_config(layout="wide")
image,image2,image3,image4,image5,image6 = load_images()


forcast_collection = db.collection('Forecasts_Tower')#Forecasts_Tower
owm_forecast_collection =  db.collection('Forecasts')
timezone_diff= timedelta(hours =4)
now = datetime.now() - timezone_diff
if now.minute <= 3:
    now = now -timedelta(hours=1)

doc = forcast_collection.document(now.strftime('%Y%m%d%H00'))  # specifies the '202103171800' document
values = doc.get().to_dict()

doc_owm = owm_forecast_collection.document(now.strftime('%Y%m%d%H00'))  # specifies the '202103171800' document
values_owm = doc_owm.get().to_dict()


offset = timedelta(hours = 1)
two_days_offset = timedelta(hours = 48) 
before = now - two_days_offset 
measured_range = pd.date_range(start= before+offset,periods = 48,freq='h')
forecasted_range = pd.date_range(start= now+offset,periods = 24,freq='h')


# =============================================================================
# Tower Data
# =============================================================================
measured = pd.DataFrame(values['measured'][::-1],index = pd.to_datetime(measured_range.strftime('%Y%m%d%H00')))
forecasted = pd.DataFrame(values['forecast'],index = pd.to_datetime(forecasted_range.strftime('%Y%m%d%H00')))
forecasted.loc[measured.index[-1]]=measured.iloc[-1]
forecasted= forecasted.sort_index()

# =============================================================================
# OWM Data
# =============================================================================
measured_owm = pd.DataFrame(values_owm['measured'][::-1],index = pd.to_datetime(measured_range.strftime('%Y%m%d%H00')))
forecasted_owm = pd.DataFrame(values_owm['forecast'],index = pd.to_datetime(forecasted_range.strftime('%Y%m%d%H00')))
forecasted_owm.loc[measured_owm.index[-1]]=measured_owm.iloc[-1]
forecasted_owm= forecasted_owm.sort_index()

# =============================================================================
# Load Forecast Fig
# =============================================================================
fig,new_status=make_forecast_plot(measured,forecasted)
fig_owm,_=make_forecast_plot(measured_owm,forecasted_owm)


img, Logo =st.columns((3,1))

st.title('Sistema de pronostico y alerta temprana ante heladas')
Logo.image(image, use_column_width=True)
img.image(image2, use_column_width=True)


st.markdown(new_status, unsafe_allow_html=True)

col1, col2 = st.columns(2)

col1.metric("Temperatura Registrada", str(round(measured[0][-1],2))+" °C", str(round(measured[0][-1]-measured[0][-2], 2))+" °C")
col2.metric("Temperatura Mínima  Pronosticada", str(round(np.min(forecasted[0]),2))+" °C")
col1.metric("Temperatura Promedio", str(round(np.mean(measured[0]),2))+" °C")
col2.metric("Temperatura Mínima  Registrada",  str(round(np.min(measured[0]),2))+" °C")

st.header("Grafico del pronóstico de la temperatura : UAC Batallas")
st.plotly_chart(fig)

st.markdown(":information_source:")
info = st.button('Haga clic aquí para obtener más información sobre el grafico')
if info:
    st.write('El gráfico muestra principalmente dos áreas: La parte de la izquierda, con fondo azul, muestra los valores de temperatura medidos en las 48 horas anteriores (línea azul).')
    st.write('La parte de la derecha, con fondo rosa claro, muestra la previsión de temperatura para las próximas 24 horas (línea roja), esta parte también contiene el intervalo de confianza para la previsión esta representa los posibles valores de la previsión considerando los errores pasados.')
    st.write('En la parte inferior se marca una linea punteada negra alrededor de los 0 grados Celsius, este representa el punto en que la temperatura hace referencia a un evento de helada.')
    st.write('El punto en que la linea que representa la temperatura cambia de azul a rojo, da a conocer la hora en que se ha producido una actualización del pronóstico. Esta ocurre con una frecuencia de una hora.')
    if st.button('Ocultar Informacion'):
        info = False
else:
    pass


Info_heladas, info_foto =st.columns((2,1))
Info_heladas.header("Las Heladas")
Info_heladas.write("La helada es un evento meteorológico que hace referencia al momento en que la temperatura del aire medida a una altura entre 1.25m y 2m  es igual o menor a 0 °C.")
Info_heladas.write("La condición que puede generar el daño en los cultivos es denominada como: Congelación, esta ocurre al momento que el agua extracelular dentro de la planta se congela.")
Info_heladas.write("El daño se produce cuando la temperatura del tejido de las plantas cae por debajo de una Temperatura Crítica la cual puede producir el funcionamiento incorrecto o la muerte de las células de las plantas.")
st.header("Tabla de rangos de temperatura para la agricultura local")
info_foto.image(image3, use_column_width=True)

critic_temperatures  = pd.DataFrame({'Temperatura Optima [°C]': ["Entre 4 y 8", "Entre 9 y 16", "Entre 12 y 23","Entre 5 y 20"],
                   
                   "Temperatura Critica [°C]": [" Menor a 1 "," Menor a -8 y Mayor a 26","Menor a 0","Menor a 0 Mayor a 30" ],
                   "Temperatura Letal [°C]":["Menor a -7","Menor a -11 y Mayor a 30","Menor a -2","Menor a -4"]},
                  index=['Papa', 'Quinua',"Cebolla","Haba"])

st.table(critic_temperatures)
# st.write()

Info_project,project_foto =st.columns((2,1))
project_foto.image(image4.transpose(Image.ROTATE_90), use_column_width=True)
Info_project.header("Sistema propuesto")
Info_project.write("El sistema propuesto cuenta de tres elementos: la adquisición de datos meteorológicos, el almacenamiento y procesamiento de los datos y los medios de notificación de alerta.")
Info_project.write("Mediante una Estacion meteorológica implementada en la granja de la UAC Batallas es que se toma las mediciones de temperatura y humedad. De manera auxiliar también son recolectadas las mismas variables a través del la plataforma de Open Weather Map.")
Info_project.write("Los datos recolectados son empleados como entrada a una red neuronal profunda. Esto permite realizar el pronostico de la temperatura ambiente para las proximás 24 horas.")
Info_project.write("Los resultados obtenidos son desplegados en esta página web. Adicionalmente si es que un evento de helada ha sido pronosticado, una alerta mediante SMS es enviada.")
Info_project.write("El objetivo del proyecto es poder brindar de mayor información al agricultor respecto a la posible ocurrencia de un evento de helada. Esto con el fin de que se puedan realizar las medidas de protección de manera más oportuna.")

Frost_freq = {'1500-2000': ['3.1','2.9','0.3','0','0','0','0','0','0','0','0.5','3.8','10.6'], 
              '2000-2500': ['5.1','2.4','0.7','0','0','0','0','0','0','0','9.1','5.1','22.4'],
              '2500-3000': ['3.1','0.6','0.3','0.1','0','0','0','0','0','0.2','0.6','3.3','8.2'],
              '3000-3500': ['22','17','5.5','1.3','0.4','0','0','0','0.2','2.5','14.4','21.1','84.8'],
              '3500-4000': ['29','24','11.5','6.3','4.4','1.3','0.7','0.6','2.1','10.2','21.2','27.4','138.5'],
              '4000-4500': ['31','29.1','23.1','21.5','18','16.1','15.1','13.4','17.9','20.5','26.2','29.7','262']}
Frost_freq_index = ["Jul","Ago","Sep","Oct","Nov","Dic","Ene","Feb","Mar","Abr","May","Jun","Total anual"]

frost_table = pd.DataFrame.from_dict(Frost_freq)
frost_table.index=Frost_freq_index

freq_foto,freq_Info=st.columns((1,1.8))
freq_Info.header("Promedio de días con presencia de Helada según la altura (m.s.n.m)")
freq_Info.table(frost_table)

freq_foto.header(" ")
freq_foto.image(image5, use_column_width=True)


st.header("Grafico del pronóstico de la temperatura : UAC Batallas (OWM)") 
st.write("De manera auxiliar se recolectan las variables de temperatura ambiente y humedad del servicio publico de meteorología de Open WeatherMap")
st.write("Esto permite tener un respaldo en caso de que alguna falla en el sistema, si bien estos datos son similares a los del área de estudio, no son muy precisos al respecto. Use la información provista por este grafico con precaución.")

st.plotly_chart(fig_owm)


st.header("Revisión de pronósticos previos.") 

date_colum, hor_colum, _ =st.columns(3)
check_date = date_colum.date_input('Seleccione una fecha',now-timedelta(hours=24),max_value=now-timedelta(hours=24))
check_hour = hor_colum.selectbox(
'Selecciona la hora del día',
('00:00','01:00','02:00','03:00','04:00','05:00','06:00','07:00',
 '08:00','09:00','10:00','11:00','12:00','13:00','14:00','15:00',
 '16:00','17:00','18:00','19:00','20:00','21:00','22:00','23:00',))
check_id_forecasted = check_date.strftime('%Y%m%d')+check_hour[:2]+'00'
check_id_measured = (check_date+timedelta(hours=24)).strftime('%Y%m%d')+check_hour[:2]+'00'

dt_f = datetime.combine(check_date, time(hour=int(check_hour[:2])))
dt_m = datetime.combine(check_date+timedelta(hours=24), time(hour=int(check_hour[:2])))

check_measured_range = pd.date_range(end=dt_m ,periods = 24,freq='h')
check_forecasted_range = pd.date_range(start=dt_f+offset,periods = 24,freq='h')

check_doc_forecasted = forcast_collection.document(check_id_forecasted).get().to_dict()
check_doc_measured = forcast_collection.document(check_id_measured).get().to_dict()

check_doc_forecasted_owm = owm_forecast_collection.document(check_id_forecasted).get().to_dict()
check_doc_measured_owm = owm_forecast_collection.document(check_id_measured).get().to_dict()


st.subheader('Pronóstico de la temperatura : Batallas')
try:
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=check_measured_range, y=check_doc_measured['measured'][-25::-1], name= 'Temperatura observada',showlegend=True))
    fig2.add_trace(go.Scatter(x=check_forecasted_range, y=check_doc_forecasted['forecast'], name= 'Temperatura pronosticada',showlegend=True))
    
    fig2.update_xaxes(title_text= 'Tiempo')
    fig2.update_yaxes(title_text= 'Temperatura [°C]')   
    fig2.update_layout(height=400, width=900,
                       legend=dict( orientation="h", yanchor="bottom", y=1.02,
                                       xanchor="right",  x=1))

    st.plotly_chart(fig2)
except:
    st.info('No se pudo encontrar los datos necesarios para desplegar el grafico, intenta otra fecha.')

st.subheader('Pronóstico de la temperatura : Batallas (Open WeatherMap)')
try:
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(x=check_measured_range, y=check_doc_measured_owm['measured'][-25::-1], name= 'Temperatura observada',showlegend=True))
    fig3.add_trace(go.Scatter(x=check_forecasted_range, y=check_doc_forecasted_owm['forecast'], name= 'Temperatura pronosticada',showlegend=True))
    fig3.update_xaxes(title_text= 'Tiempo')
    fig3.update_yaxes(title_text= 'Temperatura [°C]')   
    fig3.update_layout(height=400, width=900,
                       legend=dict( orientation="h", yanchor="bottom", y=1.02,
                                           xanchor="right",  x=1))
    st.plotly_chart(fig3)
except:
    st.info('No se pudo encontrar los datos necesarios para desplegar el grafico, intenta otra fecha.')

_,imt_logo,_=st.columns(3)
imt_logo.image(image6, use_column_width=True)
