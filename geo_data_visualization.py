import pymysql
import pandas as pd
import streamlit as st
import plotly.express as px
import os
import json
import requests

def create_mysql_connection():
    try:
        connection = pymysql.connect(
            host="localhost",
            user="root",
            password="!QAZ2wsx#EDC",
            database="phonepe_pulse"
        )
        return connection
    except pymysql.MySQLError as e:
        st.error(f"Error: {e}")
        return None

# Configuring Streamlit GUI
st.set_page_config(layout='wide')

# Function to download and load GeoJSON
@st.cache_resource
def load_geojson():
    try:
        url = "https://gist.githubusercontent.com/jbrobst/56c13bbbf9d97d187fea01ca62ea5112/raw/e388c4cae20aa53cb5090210a42ebb9b765c0a36/india_states.geojson"
        response = requests.get(url)
        response.raise_for_status()  # Check if the request was successful
        geojson_data = response.json()
        return geojson_data
    except requests.exceptions.RequestException as e:
        st.error(f"Error downloading the GeoJSON file: {e}")
        return None

# Load GeoJSON data
geojson_data = load_geojson()

def main():
    # Title
    st.header(':violet[PhonePe Pulse Data Visualization]')
    st.write('Transaction, User and Insurance based analysis in the span of year **2018** to **2024** in **INDIA**')

    # Selection option
    option = st.radio('**Select an option**', ('All India', 'State wise', 'Top categories'), horizontal=True)

    # Function to execute a query and return the result as a DataFrame
    def execute_query(query):
        connection = create_mysql_connection()
        if connection is not None:
            cursor = connection.cursor()
            try:
                cursor.execute(query)
                result = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                return pd.DataFrame(result, columns=columns)
            except Exception as e:
                st.error(f"Error: {e}")
                return None
            finally:
                cursor.close()
                connection.close()
        else:
            return None

    if option == 'All India':
        # Select tab
        tab1, tab2, tab3 = st.tabs(['Transaction', 'User', 'Insurance'])

        with tab1:
            col1, col2, col3 = st.columns(3)
            with col1:
                trans_year = st.selectbox('**Select Year**', ('2018', '2019', '2020', '2021', '2022', '2023', '2024'), key='trans_year')
            with col2:
                trans_quarter = st.selectbox('**Select Quarter**', ('1', '2', '3', '4'), key='trans_quarter')
            with col3:
                trans_type = st.selectbox('**Select Transaction type**',
                                          ('Recharge & bill payments', 'Peer-to-peer payments',
                                           'Merchant payments', 'Financial Services', 'Others'), key='trans_type')
                
            # SQL Query to fetch Transaction Analysis details
            query1 = f"SELECT STATE, TRANSACTION_AMOUNT FROM aggregate_trans WHERE YEAR = {trans_year} AND QUARTER = {trans_quarter} AND TRANSACTION_TYPE = '{trans_type}';"
            trans_qry_rslt = execute_query(query1)
            

            if trans_qry_rslt is not None:
                trans_qry_rslt = trans_qry_rslt.astype({'TRANSACTION_AMOUNT': 'float'})
                
                if geojson_data:
                    fig_tra = px.choropleth(
                        trans_qry_rslt,
                        geojson=geojson_data,
                        featureidkey='properties.ST_NM',
                        locations='STATE',
                        color='TRANSACTION_AMOUNT',
                        color_continuous_scale='Viridis',
                        title='Transaction Analysis'
                    )
                    fig_tra.update_geos(fitbounds="locations", visible=False)
                    fig_tra.update_layout(title_font=dict(size=33), title_font_color='#6739b7', height=800)
                    st.plotly_chart(fig_tra, use_container_width=True)
                else:
                    st.error("Failed to load GeoJSON data. Map cannot be displayed.")
            else:
                    st.warning("No data available for the selected filters.")

            query2 = f"SELECT STATE, TRANSACTION_COUNT, TRANSACTION_AMOUNT FROM aggregate_trans WHERE YEAR = {trans_year} AND QUARTER = {trans_quarter} AND TRANSACTION_TYPE = '{trans_type}';"
            trans_analy_rslt = execute_query(query2)
            st.header(':violet[Total calculation]')
            col4, col5 = st.columns(2)
            with col4:
                st.subheader('Transaction Analysis')
                st.dataframe(trans_analy_rslt)
            with col5:
                query3 = f"SELECT SUM(TRANSACTION_AMOUNT) AS Total, AVG(TRANSACTION_AMOUNT) AS Average FROM aggregate_trans WHERE YEAR = {trans_year} AND QUARTER = {trans_quarter} AND TRANSACTION_TYPE = '{trans_type}';"
                total_trans_amt = execute_query(query3)
                st.subheader('Transaction Amount')
                st.dataframe(total_trans_amt)

                query4 = f"SELECT SUM(TRANSACTION_COUNT) AS Total, AVG(TRANSACTION_COUNT) AS Average FROM aggregate_trans WHERE YEAR = {trans_year} AND QUARTER = {trans_quarter} AND TRANSACTION_TYPE = '{trans_type}';"
                total_trans_count = execute_query(query4)
                st.subheader('Transaction Count')
                st.dataframe(total_trans_count)

        with tab2:
            col1, col2 = st.columns(2)
            with col1:
                user_year = st.selectbox('**Select Year**', ('2018', '2019', '2020', '2021', '2022'), key='user_year')
            with col2:
                user_qtr = st.selectbox('**Select Quarter**', ('1'), key='user_qtr')

            query5 = f"SELECT STATE, SUM(TRANSACTION_COUNT) AS User_Count FROM aggregate_user WHERE YEAR = {user_year} AND QUARTER = {user_qtr} GROUP BY STATE;"
            user_qry_rslt = execute_query(query5)

            if user_qry_rslt is not None:
                user_qry_rslt = user_qry_rslt.astype({'User_Count': 'float'})
                if geojson_data:
                    fig_use = px.choropleth(
                        user_qry_rslt,
                        geojson=geojson_data,
                        featureidkey='properties.ST_NM',
                        locations='STATE',
                        color='User_Count',
                        color_continuous_scale='Viridis',
                        title='User Analysis'
                    )
                    
                    fig_use.update_geos(fitbounds="locations", visible=False)
                    fig_use.update_layout(title_font=dict(size=33), title_font_color='#6739b7', height=800)
                    st.plotly_chart(fig_use, use_container_width=True)
                else:
                    st.error("Failed to load GeoJSON data. Map cannot be displayed.")

                query6 = f"SELECT SUM(Transaction_count) AS Total, AVG(Transaction_count) AS Average FROM aggregate_user WHERE YEAR = {user_year} AND QUARTER = {user_qtr};"
                total_user_count = execute_query(query6)

                st.header(':violet[Total calculation]')
                col3, col4 = st.columns(2)
                with col3:
                    st.subheader('User Analysis')
                    st.dataframe(user_qry_rslt)
                with col4:
                    st.subheader('User Count')
                    st.dataframe(total_user_count)
        
        with tab3:
            col1, col2 = st.columns(2)
            with col1:
                ins_year = st.selectbox('**Select Year**', ('2020', '2021', '2022', '2023', '2024'), key='ins_year')
            with col2:
                ins_quarter = st.selectbox('**Select Quarter**', ('1', '2', '3', '4'), key='ins_quarter')
            

            # SQL Query to fetch Insurance Analysis details
            query7 = f"SELECT STATE, TRANSACTION_AMOUNT FROM aggregate_insu WHERE YEAR = {ins_year} AND QUARTER = {ins_quarter} ;"
            ins_qry_rslt = execute_query(query7)

            if ins_qry_rslt is not None:
                ins_qry_rslt = ins_qry_rslt.astype({'TRANSACTION_AMOUNT': 'float'})
                if geojson_data:
                    fig_ins = px.choropleth(
                        ins_qry_rslt,
                        geojson=geojson_data,
                        featureidkey='properties.ST_NM',
                        locations='STATE',
                        color='TRANSACTION_AMOUNT',
                        color_continuous_scale='thermal',
                        title='Insurance Analysis'
                    )
                    fig_ins.update_geos(fitbounds="locations", visible=False)
                    fig_ins.update_layout(title_font=dict(size=33), title_font_color='#6739b7', height=800)
                    st.plotly_chart(fig_ins, use_container_width=True)
                else:
                    st.error("Failed to load GeoJSON data. Map cannot be displayed.")

                query8 = f"SELECT STATE, TRANSACTION_COUNT, TRANSACTION_AMOUNT FROM aggregate_insu WHERE YEAR = {ins_year} AND QUARTER = {ins_quarter} ;"
                ins_analy_rslt = execute_query(query8)
                st.header(':violet[Total calculation]')
                col4, col5 = st.columns(2)
                with col4:
                    st.subheader('Insurance Analysis')
                    st.dataframe(ins_analy_rslt)
                with col5:
                    query9 = f"SELECT SUM(TRANSACTION_AMOUNT) AS Total, AVG(TRANSACTION_AMOUNT) AS Average FROM aggregate_insu WHERE YEAR = {ins_year} AND QUARTER = {ins_quarter} ;"
                    total_ins_amt = execute_query(query9)
                    st.subheader('Insurance Amount')
                    st.dataframe(total_ins_amt)

                    query10 = f"SELECT SUM(TRANSACTION_COUNT) AS Total, AVG(TRANSACTION_COUNT) AS Average FROM aggregate_insu WHERE YEAR = {ins_year} AND QUARTER = {ins_quarter} ;"
                    total_ins_count = execute_query(query10)
                    st.subheader('Insurance Count')
                    st.dataframe(total_ins_count)

    elif option == 'State wise':
        tab4, tab5 = st.tabs(['Transaction', 'User'])

        with tab4:
            col1, col2, col3 = st.columns(3)
            with col1:
                state_trans = st.selectbox('**Select State**', (
                    'Andaman & Nicobar Islands', 'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar',
                    'Chandigarh', 'Chhattisgarh', 'Dadra & Nagar Haveli & Daman & Diu', 'Delhi', 'Goa', 'Gujarat', 'Haryana',
                    'Himachal Pradesh', 'Jammu & Kashmir', 'Jharkhand', 'Karnataka', 'Kerala', 'Ladakh', 'Lakshadweep',
                    'Madhya Pradesh', 'Maharashtra', 'Manipur', 'Meghalaya', 'Mizoram', 'Nagaland', 'Odisha', 'Puducherry',
                    'Punjab', 'Rajasthan', 'Sikkim', 'Tamil Nadu', 'Telangana', 'Tripura', 'Uttar Pradesh', 'Uttarakhand',
                    'West Bengal'), key='st_tr_st')
            with col2:
                state_trans_yr = st.selectbox('**Select Year**', ('2018', '2019', '2020', '2021', '2022', '2023', '2024'), key='state_trans_yr')
            with col3:
                st_tr_qtr = st.selectbox('**Select Quarter**', ('1', '2', '3', '4'), key='st_tr_qtr')

            query11 = f"SELECT TRANSACTION_TYPE, TRANSACTION_AMOUNT FROM aggregate_trans WHERE STATE = '{state_trans}' AND YEAR = {state_trans_yr} AND QUARTER = {st_tr_qtr};"
            st_trans_qry_rslt = execute_query(query11)

            if st_trans_qry_rslt is not None:
                st_trans_qry_rslt = st_trans_qry_rslt.astype({'TRANSACTION_AMOUNT': 'float'})
                fig_st_trans = px.bar(
                    st_trans_qry_rslt, x='TRANSACTION_TYPE', y='TRANSACTION_AMOUNT', color='TRANSACTION_AMOUNT',
                    color_continuous_scale='thermal', title='Transaction Analysis Chart', height=500)
                fig_st_trans.update_layout(title_font=dict(size=33), title_font_color='#6739b7')
                st.plotly_chart(fig_st_trans, use_container_width=True)

                query12 = f"SELECT TRANSACTION_TYPE, TRANSACTION_COUNT, TRANSACTION_AMOUNT FROM aggregate_trans WHERE STATE = '{state_trans}' AND YEAR = {state_trans_yr} AND QUARTER = {st_tr_qtr};"
                st_trans_analy_qry_rslt = execute_query(query12)

                query13 = f"SELECT SUM(TRANSACTION_AMOUNT) AS Total, AVG(TRANSACTION_AMOUNT) AS Average FROM aggregate_trans WHERE STATE = '{state_trans}' AND YEAR = {state_trans_yr} AND QUARTER = {st_tr_qtr};"
                total_st_trans_amt = execute_query(query13)

                query14 = f"SELECT SUM(TRANSACTION_COUNT) AS Total, AVG(TRANSACTION_COUNT) AS Average FROM aggregate_trans WHERE STATE = '{state_trans}' AND YEAR = {state_trans_yr} AND QUARTER = {st_tr_qtr};"
                total_st_trans_count = execute_query(query14)

                st.header(':violet[Total calculation]')
                col4, col5 = st.columns(2)
                with col4:
                    st.subheader('Transaction Analysis')
                    st.dataframe(st_trans_analy_qry_rslt)
                with col5:
                    st.subheader('Transaction Amount')
                    st.dataframe(total_st_trans_amt)
                    st.subheader('Transaction Count')
                    st.dataframe(total_st_trans_count)

        with tab5:
            col5, col6 = st.columns(2)
            with col5:
                st_user = st.selectbox('**Select State**', (
                    'Andaman & Nicobar Islands', 'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar',
                    'Chandigarh', 'Chhattisgarh', 'Dadra & Nagar Haveli & Daman & Diu', 'Delhi', 'Goa', 'Gujarat', 'Haryana',
                    'Himachal Pradesh', 'Jammu & Kashmir', 'Jharkhand', 'Karnataka', 'Kerala', 'Ladakh', 'Lakshadweep',
                    'Madhya Pradesh', 'Maharashtra', 'Manipur', 'Meghalaya', 'Mizoram', 'Nagaland', 'Odisha', 'Puducherry',
                    'Punjab', 'Rajasthan', 'Sikkim', 'Tamil Nadu', 'Telangana', 'Tripura', 'Uttar Pradesh', 'Uttarakhand',
                    'West Bengal'), key='st_us_st')
            with col6:
                st_us_yr = st.selectbox('**Select Year**', ('2018', '2019', '2020', '2021', '2022', '2023', '2024'), key='st_us_yr')

            query15 = f"SELECT QUARTER, SUM(Transaction_count) AS User_Count FROM aggregate_user WHERE STATE = '{st_user}' AND YEAR = {st_us_yr} GROUP BY QUARTER;"
            st_user_qry_rslt = execute_query(query15)

            if st_user_qry_rslt is not None:
                st_user_qry_rslt = st_user_qry_rslt.astype({'User_Count': 'int'})
                fig_st_user = px.bar(
                    st_user_qry_rslt, x='QUARTER', y='User_Count', color='User_Count', color_continuous_scale='thermal',
                    title='User Analysis Chart', height=500)
                fig_st_user.update_layout(title_font=dict(size=33), title_font_color='#6739b7')
                st.plotly_chart(fig_st_user, use_container_width=True)

                query16 = f"SELECT SUM(TRANSACTION_COUNT) AS Total, AVG(TRANSACTION_COUNT) AS Average FROM aggregate_user WHERE STATE = '{st_user}' AND YEAR = {st_us_yr};"
                total_st_user_count = execute_query(query16)

                st.header(':violet[Total calculation]')
                col3, col4 = st.columns(2)
                with col3:
                    st.subheader('User Analysis')
                    st.dataframe(st_user_qry_rslt)
                with col4:
                    st.subheader('User Count')
                    st.dataframe(total_st_user_count)

    else:
        tab6, tab7 = st.tabs(['Transaction', 'User'])

        with tab6:
            top_tr_yr = st.selectbox('**Select Year**', ('2018', '2019', '2020', '2021', '2022', '2023', '2024'), key='top_tr_yr')

            query17 = f"SELECT State, SUM(TRANSACTION_AMOUNT) AS Transaction_amount FROM top_trans WHERE YEAR = {top_tr_yr} GROUP BY State ORDER BY Transaction_amount DESC LIMIT 10;"
            top_tr_qry_rslt = execute_query(query17)

            if top_tr_qry_rslt is not None:
                top_tr_qry_rslt = top_tr_qry_rslt.astype({'Transaction_amount': 'float'})
                fig_top_tr = px.bar(
                    top_tr_qry_rslt, x='State', y='Transaction_amount', color='Transaction_amount',
                    color_continuous_scale='thermal', title='Top Transaction Analysis Chart', height=600)
                fig_top_tr.update_layout(title_font=dict(size=33), title_font_color='#6739b7')
                st.plotly_chart(fig_top_tr, use_container_width=True)

                query18 = f"SELECT State, SUM(TRANSACTION_AMOUNT) AS Transaction_amount, SUM(TRANSACTION_COUNT) AS Transaction_count FROM top_trans WHERE Year = {top_tr_yr} GROUP BY State ORDER BY Transaction_amount DESC LIMIT 10;"
                top_tr_analy_qry_rslt = execute_query(query18)

                st.header(':violet[Total calculation]')
                st.subheader('Top Transaction Analysis')
                st.dataframe(top_tr_analy_qry_rslt)

        with tab7:
            top_us_yr = st.selectbox('**Select Year**', ('2018', '2019', '2020', '2021', '2022', '2023', '2024'), key='top_us_yr')

            query19 = f"SELECT State, SUM(REGISTERED_USERS) AS Top_user FROM top_user WHERE YEAR={top_us_yr} GROUP BY State ORDER BY Top_user DESC LIMIT 10;"
            top_us_qry_rslt = execute_query(query19)

            if top_us_qry_rslt is not None:
                top_us_qry_rslt = top_us_qry_rslt.astype({'Top_user': 'int'})
                fig_top_us = px.bar(
                    top_us_qry_rslt, x='State', y='Top_user', color='Top_user', color_continuous_scale='thermal',
                    title='Top User Analysis Chart', height=600)
                fig_top_us.update_layout(title_font=dict(size=33), title_font_color='#6739b7')
                st.plotly_chart(fig_top_us, use_container_width=True)

                st.header(':violet[Total calculation]')
                st.subheader('Total User Analysis')
                st.dataframe(top_us_qry_rslt)

if __name__ == "__main__":
    main()
