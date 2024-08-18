import pandas as pd
import streamlit as st
import pydeck as pdk

from api.OpenAICaller import OpenAICaller
from api.ZillowApiCaller import ZillowApiCaller

st.title('Zillow Zestimate Area Analysis')
st.sidebar.title('Filters')


zillow_api_caller = ZillowApiCaller()
open_api_caller = OpenAICaller()
city = st.sidebar.text_input('Enter City', placeholder='Hoboken')
state = st.sidebar.text_input('Enter State', placeholder='NJ')
min_bedrooms = st.sidebar.number_input('Bedrooms', value=1, min_value=1)
exact_bedrooms_checkbox = st.sidebar.checkbox('Exact number of bedrooms')
min_bathrooms = st.sidebar.number_input('Bathrooms', value=1, min_value=1)
exact_bathrooms_checkbox = st.sidebar.checkbox('Exact number of bathrooms')
min_price = st.sidebar.number_input('Min price', value=2500, min_value=1)
max_price = st.sidebar.number_input('Max price', value=4000, min_value=1)
search_button = st.sidebar.button('Search')

if city and state and min_bedrooms and min_bathrooms and min_price and max_price and search_button:
    bedrooms_text = f"exactly {min_bedrooms}" if exact_bedrooms_checkbox else f"at least {min_bedrooms}"
    bathrooms_text = f"exactly {min_bathrooms}" if exact_bathrooms_checkbox else f"at least {min_bathrooms}"
    st.write(f"Fetching data for {city}, {state} with {bedrooms_text} bedrooms, {bathrooms_text} bathrooms.")
    rental_collection = zillow_api_caller.fetch_pages_for_city(city=city, state=state, min_price=min_price,
                                                               max_price=max_price, baths_min=min_bathrooms,
                                                               beds_min=min_bedrooms, exact_bathrooms=exact_bathrooms_checkbox, exact_bedrooms=exact_bedrooms_checkbox)
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
        def make_google_search_link(address):
            query = address.replace(' ', '+')
            url = f'https://www.google.com/search?q={query}'
            return f'<a href="{url}" target="_blank">{address}</a>'

        df_html = input_df.to_html(index=False, escape=False, formatters={'Address': make_google_search_link})

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
                    a {{ color: blue; text-decoration: underline; }}
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
        f"{city}_{state}_{min_bedrooms}_{exact_bedrooms_checkbox}_{min_bathrooms}_{exact_bathrooms_checkbox}_{current_date}.csv",
        "text/csv",
        key='download-csv'
    )
else:
    st.write("Please enter your city, and state to fetch data.")
