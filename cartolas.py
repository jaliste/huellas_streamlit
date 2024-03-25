# streamlit_app.py

import streamlit as st
from streamlit_gsheets import GSheetsConnection
import streamlit.components.v1 as components
import json
import pandas as pd
from babel.numbers import format_decimal as format_number
from st_mui_table import st_mui_table

from password import check_password
import extra_streamlit_components as stx

cookie_manager = stx.CookieManager()

logged_in = cookie_manager.get("__huellas_verdes__")
if logged_in is None:
    if not check_password():
        st.stop()  # Do not continue if check_password is not True.
    cookie_manager.set("__huellas_verdes__","LOGGED_IN")

# Create a connection object.
conn = st.connection("gsheets", type=GSheetsConnection)
# CobrosYAbonos2023
df_ruts = conn.read(worksheet="RutSocios")
ruts = list(set(df["RUT"].tolist()))
ruts.sort()


df = conn.read(worksheet="invoices",unformatted_columns=["Fecha"])
df = df.dropna(how='all').fillna('')
df_abonos = conn.read(worksheet="abonos",unformatted_columns=["Fecha"])
df_abonos = df_abonos.dropna(how='all').fillna('')
df_abonos=df_abonos[df_abonos["TipoAbono"]=="CuotaSocial"]
df_abonos = df_abonos[['Fecha','Rut','Socio','Descripción','Abono','Cargo']]
df_abonos["Detalle"]=df_abonos["Descripción"]
df_abonos["Descripción"]="Abono por transferencia"

df_deuda = conn.read(worksheet="deuda.inicial",unformatted_columns=["Fecha"])
df_deuda = df_deuda.dropna(how='all').fillna(0)
df_deuda = df_deuda[["Fecha","Rut","Socio","Descripción","Abono","Cargo"]]


rutCookie = cookie_manager.get("__huellas_verdes_RUT__")
if rutCookie is None:
    rut = st.sidebar.selectbox("Elige tu rut",["-"]+ruts,index=0,format_func = lambda x: x)
    if rut=="-":
        st.stop()
    else:
        cookie_manager.set("__huellas_verdes_RUT__",rut,key="set2")
else:
    rut = rutCookie
df = df[df['Rut']==rut]
df["Cargo"] = df["Total"]
df["Abono"] = 0
df=df.drop("Total",axis=1)
df_abonos = df_abonos[df_abonos['Rut']==rut]
df_deuda = df_deuda[df_deuda['Rut']==rut]

df_details = conn.read(worksheet="invoice_details",unformatted_columns=["Fecha"])
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
st.title("Cooperativa Huellas Verdes")
st.header("Abonos y Cargos Cuotas Sociales")
def cambiar_socio():
    cookie_manager.delete("__huellas_verdes_RUT__")
    st.stop()
c1,c2=st.columns(2)
with c1:
    st.markdown("**Socia(o):**\t"+list(df3['Socio'])[0])
    st.markdown("**Rut:**\t"+rut)
with c2:
    button=st.button("Cambiar Socio",on_click=cambiar_socio)

tabPre,tab2024,tab2023,tabExtras = st.tabs(["Precobro","2024","2023","Extras 2022"])
with tabPre:
    st.subheader("Pronto")
with tab2024:
    st.subheader("Pronto")
with tabExtras:
    st.subheader("Pronto")
with tab2023:

    st.subheader("Resumen")
    abono = sum(df3["Abono"])
    cargo = sum(df3["Cargo"])
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
    df4 = df3[["Fecha","Descripción","Cargo","Abono","Invoice"]]
#rows = st_mui_table(df3, details, groupby="First Name")
    rows = st_mui_table(df4,
                        enablePagination=False,
                        detailData=details,
                        detailColumns=["Invoice"]
                        )

if rows:
    st.write("You have selected", rows)

