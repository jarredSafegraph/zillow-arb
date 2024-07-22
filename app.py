import pandas as pd
import streamlit as st
import pydeck as pdk

from api.OpenAICaller import OpenAICaller
from api.ZillowApiCaller import ZillowApiCaller

st.title('Zillow Zestimate Area Analysis')
st.sidebar.title('Filters')

zillow_api_caller = ZillowApiCaller()
open_api_caller = OpenAICaller()
city = st.sidebar.text_input('Enter city', placeholder='Hoboken')
state = st.sidebar.text_input('Enter state', placeholder='NJ')
bedrooms = st.sidebar.number_input('Bedrooms', value=1, min_value=1)
bathrooms = st.sidebar.number_input('Bathrooms', value=1, min_value=1)
min_price = st.sidebar.number_input('Min price', value=2500, min_value=1)
max_price = st.sidebar.number_input('Max price', value=4000, min_value=1)
search_button = st.sidebar.button('Search')

if city and state and bedrooms and bathrooms and min_price and max_price and search_button:
    st.write(f"Fetching data for {city}, {state} with {bedrooms} bedrooms, {bathrooms} bathrooms.")
    rental_collection = zillow_api_caller.fetch_pages_for_city(city=city, state=state, min_price=min_price,
                                                               max_price=max_price, baths_min=bathrooms,
                                                               beds_min=bedrooms)
    rental_collection.filter_by_bedrooms(bedrooms)
    rental_collection.filter_by_bathrooms(bathrooms)
    rental_collection_lat_lng = rental_collection.get_center_of_lat_lng()
    df = rental_collection.to_pandas_df()

    if df is None or df.empty:
        st.write("No rentals found for the given criteria.")
        st.stop()

    initial_view_state = pdk.ViewState(
        latitude=rental_collection_lat_lng[0],
        longitude=rental_collection_lat_lng[1],
        zoom=12
    )

    layer = pdk.Layer(
        'ScatterplotLayer',
        df,
        get_position='[Longitude, Latitude]',
        get_color='color',
        auto_highlight=True,
        get_radius="Size",
        pickable=True,
        extruded=True
    )

    r = pdk.Deck(
        layers=[layer],
        initial_view_state=initial_view_state,
        map_style='mapbox://styles/mapbox/light-v10',
        tooltip={
            "text": "Address: {Address}\n\tUnit: {Unit}\n\tBedrooms: {Bedrooms}\n\tBathrooms: {Bathrooms}\n\tPrice: {Price}\n\tZestimate: {Zestimate}\n\tValue: {Relative Value}"}
    )

    map_clicked = st.pydeck_chart(r)

    df = df.drop(columns=['Latitude', 'Longitude', 'Size', 'color']).reset_index(drop=True)
    df_sorted = df.sort_values(by='Relative Value', ascending=True)


    def convert_df(input_df):
        df_html = input_df.to_html(index=False, escape=False, formatters=dict())

        html_with_container = f'''
            <html>
            <head>
                <script src="https://ajax.googleapis.com/ajax/libs/jquery/2.1.1/jquery.min.js"></script>
                <style>
                    .table-container {{
                        height: 400px;
                        width: 100%;
                        overflow-y: auto;
                        border: 2px solid #444;
                    }}
                    .table-container:hover {{ border-color: red; }}
                    table {{ width: 100%; border-collapse: collapse; }}
                    th, td {{ padding: 24px; background: #eee; }}
                    th {{
                        position: sticky;
                        top: 0;
                        background: #ddd;
                    }}
                </style>
            </head>
            <body>
                <div class="table-container" id="table-container">
                    {df_html}
                </div>
                <script>
                    var $container = $("#table-container");
                    function anim() {{
                        var st = $container.scrollTop();
                        var sb = $container.prop("scrollHeight") - $container.innerHeight();
                        $container.animate({{scrollTop: st < sb / 2 ? sb : 0}}, 4000, anim);
                    }}
                    function stop() {{
                        $container.stop();
                    }}
                    anim();
                    $container.hover(stop, anim);
                </script>
            </body>
            </html>
            '''
        return html_with_container

    with st.spinner('Loading summary...'):
        summary = open_api_caller.summarize_df(df_sorted)
        st.markdown(summary)
    html = convert_df(df_sorted)
    st.markdown(html, unsafe_allow_html=True)

    current_date = pd.Timestamp.now().strftime('%Y%m%d')
    st.write("\n")
    st.download_button(
        "Download",
        df_sorted.to_csv(index=False).encode('utf-8'),
        f"{city}_{state}_{bedrooms}_{bathrooms}_{current_date}.csv",
        "text/csv",
        key='download-csv'
    )
else:
    st.write("Please enter your city, and state to fetch data.")
