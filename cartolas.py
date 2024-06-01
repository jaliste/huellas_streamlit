# streamlit_app.py

import streamlit as st
from streamlit_gsheets import GSheetsConnection
import streamlit.components.v1 as components
import json
import pandas as pd
from babel.numbers import format_decimal as format_number
from st_mui_table import st_mui_table
import io
from password import check_password
import extra_streamlit_components as stx
import numpy as np

def get_cobros_abonos_raw(conn,year):
    if year=="2024":
        spreadsheet = st.secrets["cobros_abonos_2024"]
    elif year=="2023":
        spreadsheet = st.secrets["cobros_abonos_2023"]

    df = conn.read(spreadsheet=spreadsheet, worksheet="invoices",ttl="1d",unformatted_columns=["Fecha"])
    df_abonos = conn.read(spreadsheet=spreadsheet, worksheet="abonos",ttl="1d",unformatted_columns=["Fecha"])
    df_deuda = conn.read(spreadsheet=spreadsheet, worksheet="deuda.inicial",ttl="1d",unformatted_columns=["Fecha"])
    df_details = conn.read(spreadsheet=spreadsheet, worksheet="invoice_details",ttl="1d",unformatted_columns=["Fecha"])
    return df,df_abonos,df_deuda,df_details

def procesar_cobros_abonos(rut, df,df_abonos,df_deuda,df_details):    
    df = df.dropna(how='all').fillna('')
    df_abonos = df_abonos.dropna(how='all').fillna('')
    df_abonos=df_abonos[df_abonos["TipoAbono"]=="CuotaSocial"]
    df_abonos = df_abonos[['Fecha','Rut','Socio','Descripción','Abono','Cargo']]
    df_abonos["Cargo"].replace('',0,inplace=True)
    df_abonos["Abono"].replace('',0,inplace=True)
    
    df_abonos["Detalle"]=df_abonos["Descripción"]
    df_abonos["Descripción"]="Abono por transferencia"

    df_deuda = df_deuda.dropna(how='all').fillna(0)
    df_deuda = df_deuda[["Fecha","Rut","Socio","Descripción","Abono","Cargo"]]

    df = df[df['Rut']==rut]
    df["Cargo"] = df["Total"]
    df["Abono"] = 0
    df=df.drop("Total",axis=1)
    df_abonos = df_abonos[df_abonos['Rut']==rut]
    df_deuda = df_deuda[df_deuda['Rut']==rut]

    df_details = df_details.dropna(how='all').fillna('')
    details = {}
    for i,row in df.iterrows():
        invoice = row["Invoice"]
        df_di = df_details[df_details["Invoice"]==invoice]
        df_di = df_di[["Fecha","Productor","Producto","Costo","Cant","Unid","Total","Modificado"]]
        details[invoice] = df_di.to_dict('records')

    df3 = pd.concat([df,df_abonos,df_deuda])
    df3["Fecha"]=pd.to_datetime(df3["Fecha"],format="%d/%m/%Y")
    df3 = df3.sort_values(by="Fecha")
    df3['Fecha'] = df3['Fecha'].dt.strftime('%d/%m/%Y')
    #df3 = df3[['Fecha','Invoice','Producto',"Costo","Cant","Unid","Total"]]
    df3 = df3.reset_index()
    return df3,details



cookie_manager = stx.CookieManager()

logged_in = cookie_manager.get("__huellas_verdes__")
if logged_in is None:
    if not check_password():
        st.stop()  # Do not continue if check_password is not True.
    cookie_manager.set("__huellas_verdes__","LOGGED_IN")

# Create a connection object.
conn = st.connection("gsheets", type=GSheetsConnection)
# CobrosYAbonos2023

df_ruts = conn.read(spreadsheet=st.secrets["cobros_abonos_2023"],worksheet="RutSocios",ttl="1d")
df_ruts = df_ruts[["RUT"]]
df_ruts = df_ruts.dropna()
ruts = list(set(df_ruts["RUT"].tolist()))
ruts.sort()

rutCookie = cookie_manager.get("__huellas_verdes_RUT__")
if rutCookie is None:
    rut = st.sidebar.selectbox("Elige tu rut",["-"]+ruts,index=0,format_func = lambda x: x)
    if rut=="-":
        st.stop()
    else:
        cookie_manager.set("__huellas_verdes_RUT__",rut,key="set2")
else:
    rut = rutCookie

dfs = get_cobros_abonos_raw(conn,"2024")


df3_2024, details_2024 = procesar_cobros_abonos(rut,*dfs)
dfs = get_cobros_abonos_raw(conn,"2023")


df3_2023, details_2023 = procesar_cobros_abonos(rut,*dfs)

st.title("Cooperativa Huellas Verdes")
st.header("Abonos y Cargos Cuotas Sociales")
def cambiar_socio():
    cookie_manager.delete("__huellas_verdes_RUT__")
    st.stop()
c1,c2=st.columns(2)
#if (len(df3)==0):
#    st.subheader("No hay info para el RUT. Es Socio(a) pero no tiene info en la APP")
#else:    
#    with c1:
#        st.markdown("**Socia(o):**\t"+list(df3['Socio'])[0])
#        st.markdown("**Rut:**\t"+rut)
with c2:
    button=st.button("Cambiar Socio",on_click=cambiar_socio)

tabPre,tab2024,tab2023,tabExtras = st.tabs(["Precobro","2024","2023","Extras 2022"])
with tabPre:
    st.subheader("Pronto")
with tab2024:
    st.subheader("Resumen")
   
    abono = sum(df3_2024["Abono"])
    cargo = sum(df3_2024["Cargo"])
    deuda = cargo - abono
    s_abono = "$"+format_number(abono,locale='es_CL')
    s_cargo = "$"+format_number(cargo,locale='es_CL')
    s_deuda= "$"+format_number(deuda,locale='es_CL')

    st.markdown(f"<table><tr><td><b>Cargos:</td><td><b style='color:darkblue'>{s_cargo}</b></td></tr><tr><td><b>Abonos:</b></td><td><b style='color:darkblue'>{s_abono}</b></td></tr><tr><td><b>Total Deuda:</b></td><td><b style='color:darkblue'>{s_deuda}</b></td></tr></table>",unsafe_allow_html=True)
    st.subheader("Detalles")
    df4_2024 = df3_2024[["Fecha","Descripción","Cargo","Abono","Invoice"]]
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
    # Write each dataframe to a different worksheet.
        df4_2024.to_excel(writer, sheet_name='Sheet1', index=False)
        download2 = st.download_button(
        label="Descargar Excel",
        data=buffer,
        file_name='sociales2024.xlsx',
        mime='application/vnd.ms-excel'
        )
#rows = st_mui_table(df3, details, groupby="First Name")
    rows = st_mui_table(df4_2024,
                        enablePagination=False,
                        detailData=details_2024,
                        detailColumns=["Invoice"],
                        key="mui_2024"
                        )
with tabExtras:
    st.subheader("Pronto")
with tab2023:
    dfs = get_cobros_abonos_raw(conn,"2023")
    df3_2023,details_2023 = procesar_cobros_abonos(rut,*dfs)
    st.subheader("Resumen")
    abono = sum(df3_2023["Abono"])
    cargo = sum(df3_2023["Cargo"])
    deuda = cargo - abono
    s_abono = "$"+format_number(abono,locale='es_CL')
    s_cargo = "$"+format_number(cargo,locale='es_CL')
    s_deuda= "$"+format_number(deuda,locale='es_CL')

    st.markdown(f"<table><tr><td><b>Cargos:</td><td><b style='color:darkblue'>{s_cargo}</b></td></tr><tr><td><b>Abonos:</b></td><td><b style='color:darkblue'>{s_abono}</b></td></tr><tr><td><b>Total Deuda:</b></td><td><b style='color:darkblue'>{s_deuda}</b></td></tr></table>",unsafe_allow_html=True)

#  |   Abonos: | {sum(df3["Abono"])],
#    ["Cargos:",sum(df3["Cargo"])],
#    ["Total Deuda:",sum(df3["Cargo"])-sum(df3["Abono"])],
#""")
#for idx,row in df3.iterrows():
#   with st.expander("Detalles"):
#      st.dataframe(json.loads(row["Detalle"]))
#
#df = pd.DataFrame(raw_data, columns=["First Name", "Last Name", "Age"])
    st.subheader("Detalles")
    df4_2023 = df3_2023[["Fecha","Descripción","Cargo","Abono","Invoice"]]
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
    # Write each dataframe to a different worksheet.
        df4_2023.to_excel(writer, sheet_name='Sheet1', index=False)
        download2 = st.download_button(
        label="Descargar Excel",
        data=buffer,
        file_name='sociales2023.xlsx',
        mime='application/vnd.ms-excel'
        )
#rows = st_mui_table(df3, details, groupby="First Name")
    rows = st_mui_table(df4_2023,
                        enablePagination=False,
                        detailData=details_2023,
                        detailColumns=["Invoice"],
                        key="mui_2023"
                        )



