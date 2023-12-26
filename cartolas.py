# streamlit_app.py

import streamlit as st
from streamlit_gsheets import GSheetsConnection
import streamlit.components.v1 as components
import json
import pandas as pd
from my_data_table import my_data_table
from babel.numbers import format_decimal as format_number


import hmac
import streamlit as st


def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if hmac.compare_digest(st.session_state["password"], st.secrets["password"]):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store the password.
        else:
            st.session_state["password_correct"] = False

    # Return True if the password is validated.
    if st.session_state.get("password_correct", False):
        return True

    # Show input for password.
    st.text_input(
        "Contraseña", type="password", on_change=password_entered, key="password"
    )
    if "password_correct" in st.session_state:
        st.error("😕 Contraseña incorrecta")
    return False


if not check_password():
    st.stop()  # Do not continue if check_password is not True.

# Create a connection object.
conn = st.connection("gsheets", type=GSheetsConnection)
# CobrosYAbonos2023

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

ruts = list(set(df["Rut"].tolist()))
ruts.sort()
rut = st.sidebar.selectbox("Elige tu rut",["-"]+ruts,index=0,format_func = lambda x: x)
if rut=="-":
    st.stop()
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

df3 = pd.concat([df,df_abonos,df_deuda]).sort_values(by="Fecha")

#df3 = df3[['Fecha','Invoice','Producto',"Costo","Cant","Unid","Total"]]
df3 = df3.reset_index()
st.title("Cooperativa Huellas Verdes")
st.header("Abonos y Cargos Cuotas Sociales")
st.markdown("**Socia(o):**\t"+list(df3['Socio'])[0])
st.markdown("**Rut:**\t"+rut)

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
rows = my_data_table(df3, details, groupby="First Name")
if rows:
    st.write("You have selected", rows)

