# Smart Home GUI Playback Streamlit App

#Usage:
#python -m streamlit run smart_home_dashboard.py

import streamlit as st
import pandas as pd
import numpy as np
import cv2
from datetime import datetime, timedelta
from PIL import Image

import altair as alt

from matplotlib import pyplot as plt
import pandas as pd
import numpy as np
import cv2
from PIL import Image
import time

#not necessary, changes to wide
st.set_page_config(layout="wide", page_title="tm03", initial_sidebar_state="collapsed")
# open sheet



#fix this, hard coded
st.sidebar.header("Patients: ")

with open('tm003.txt') as f:
    lines = f.readlines()




data = []
######
for line in lines:
    parts = line.strip().split()
    date = parts[0]
    time = parts[1]
    sensor = parts[2]
    status = parts[3]
    activity = parts[4]
    data.append([date, time, sensor, status, activity])


st.title("Smart Home Dashboard")

df = pd.DataFrame(data, columns=["date", "time", "sensor", "status", "activity"])
originalDf = df

unique_dates = sorted(originalDf['date'].unique())
selected_date = st.sidebar.selectbox("Choose a date", unique_dates)
df = originalDf[originalDf['date'] == selected_date]

#df = df[df['date'] == "2016-11-23"]


def draw_overlay(current_room, current_action, time_str=None):
    path = "house_layout.jpg"
    overlay_width, overlay_height = 553, 485

    background = cv2.imread(path)
    background = cv2.resize(background, (overlay_width, overlay_height))


    overlay = background.copy()
    rooms = {
        "BedroomA": (76, 356, 198, 127),
        "Closet": (76, 290, 76, 66),
        "BathroomA": (153, 290, 58, 66),
        "BedroomB": (9, 153, 126, 125),
        "OfficeA": (136, 153, 130, 126),
        "LivingRoomA": (339, 141, 194, 137),
        "KitchenA": (401, 25, 131, 113),
        "BathroomB": (107, 25, 79, 87),
        "UtilityRoomA": (9, 26, 96, 86),
        "DiningA": (270, 26, 91, 90),
        "Garage": (340, 360, 198, 120)
    }

    # Draw rooms
    for room_name, (x, y, w, h) in rooms.items():
        color = (154, 205, 50)  # light green
        thickness = -1  # filled
        if room_name in current_room:
            color = (0, 165, 255)  # orange for current room
            thickness = -1
            # Add thick border around current room
            cv2.rectangle(overlay, (x, y), (x + w, y + h), (0, 0, 255), 3)  # red border
        cv2.rectangle(overlay, (0,0), (553, 28), (80, 80, 80), -1)
        cv2.putText(overlay, "Activity: " + current_action, (10, 22), cv2.FONT_HERSHEY_SIMPLEX, .8, (80, 255, 80), 1)
        

    # Draw the time string
    if time_str:
        cv2.putText(overlay, f"Time: {time_str}", (350, 22),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 60, 255), 1)

    return overlay

##output = draw_overlay("Closet", "Walking", time_str=round(17.06721,2))

# Convert from BGR to RGB for displaying with matplotlib
#output_rgb = cv2.cvtColor(output, cv2.COLOR_BGR2RGB)

#plt.imshow(output_rgb)
#plt.axis('off')
#plt.show()

# Assume your activity switch DataFrame is named `activitydf`
activitydf = df
activitydf['activity_block'] = (activitydf['activity'] != activitydf['activity'].shift()).cumsum()
activitydf = df[df['activity'] != df['activity'].shift()].reset_index(drop=True)

# Make sure timestamp is in datetime format
activitydf['time'] = pd.to_datetime(activitydf['time'])

# Calculate duration until the next activity
activitydf['time'] = activitydf['time'].shift(-1) - activitydf['time']

# Optional: convert to seconds
activitydf['time'] = activitydf['time'].dt.total_seconds()
#activitydf['time'] = pd.to_timedelta(activitydf['time'], unit='s')

counts = df['activity_block'].value_counts().sort_index().reset_index(drop=True)
activitydf['activity_num'] = counts

#activitydf


frames = []
for _, row in activitydf.iterrows():
    current_room = row['sensor']
    current_action = row['activity']
    time_str = row['time']  # already seconds

    overlay = draw_overlay(current_room, current_action, round(time_str, 2))
    rgb_overlay = cv2.cvtColor(overlay, cv2.COLOR_BGR2RGB)
    frames.append(rgb_overlay)




leftCol, rightCol = st.columns(2)

if 'page' not in st.session_state:
    st.session_state.page = 'Home'  

if st.session_state.page == 'Home':
    with rightCol:
        st.header("GUI")
        max_index = len(frames) - 1
        index = st.slider("Scroll through activities", 0, max_index, 0)

        frame = frames[index]
        row = activitydf.iloc[index]

        st.image(frame, caption=f"{row['sensor']} - {row['activity']} {round(row['time'], 2)}s")

    with leftCol:
        activitydf
    

    st.divider()

    graphLeft, graphRight = st.columns(2)

    with graphLeft:

        with st.container():

            st.subheader("Daytime vs Nightime Bathroom")

            # Ensure datetime exists
            df['datetime'] = pd.to_datetime(df['date'] + ' ' + df['time'])

            # Define bathroom-related sensor keywords
            bathroom_keywords = ['BathroomA']
            bathroom_df = df[df['sensor'].str.contains('|'.join(bathroom_keywords))]

            # Define time period (Daytime: 07:00–21:00, Nighttime: 21:00–07:00)
            def get_time_period(dt):
                hour = dt.hour
                return 'Daytime' if 7 <= hour < 21 else 'Nighttime'

            bathroom_df['period'] = bathroom_df['datetime'].apply(get_time_period)

            # Count ON/OFF per period
            summary = bathroom_df.groupby(['period', 'status']).size().unstack(fill_value=0).reset_index()
            #summary = summary['status'] != "OFF"
            summary = summary.drop('OFF', axis = 1)
            # Show table
            #st.dataframe(summary)

            # Optional: Altair bar chart
            bar_chart = alt.Chart(summary.melt(id_vars='period')).mark_bar().encode(
                x='period:N',
                y= alt.Y('value:Q',scale=alt.Scale(domain=[0, 1000])),
                color='status:N',
                column='status:N'
            ).properties(
            width=400,
            height=300
            #title='Bathroom Activity'
            )

            st.altair_chart(bar_chart, use_container_width=False)

    with graphRight:
        with st.container():
            df['datetime'] = pd.to_datetime(df['date'] + ' ' + df['time'])
            df['activity_block'] = (df['activity'] != df['activity'].shift()).cumsum()
            start_times = df.groupby('activity_block')['datetime'].first().reset_index()

            # Merge start times into activitydf
            activitydf = activitydf.copy()
            activitydf['activity_block'] = activitydf.index + 1  # Match groupby block IDs
            activitydf = pd.merge(activitydf, start_times, on='activity_block', how='left')
            activitydf.rename(columns={'datetime': 'start_time'}, inplace=True)

            # Extract the hour
            activitydf['hour'] = activitydf['start_time'].dt.floor('H')

            # Sum activity_num per hour
            activitysums_per_hour = activitydf.groupby('hour')['activity_num'].sum().reset_index()

            # Display

            #DATAFRAME
            #st.write("Activities by Hour:")
            #st.dataframe(activitysums_per_hour)

            chart = alt.Chart(activitysums_per_hour).mark_bar().encode(
            x=alt.X('hour:T', title='Hour'),
            y=alt.Y('activity_num:Q', title='Activity', scale=alt.Scale(domain=[0, 1000])),
            tooltip=['hour', 'activity_num']
            ).properties(
            width=400,
            height=400,
            title='Total Activity Events per Hour'
            )
            st.subheader("Overall Activity")
            # Display in Streamlit
            st.altair_chart(chart, use_container_width=True)
    st.divider()
    with st.container():
        alldf = originalDf
        alldf['activity_block'] = (alldf['activity'] != alldf['activity'].shift()).cumsum()
        alldf = originalDf[originalDf['activity'] != originalDf['activity'].shift()].reset_index(drop=True)

        # Make sure timestamp is in datetime format
        alldf['time'] = pd.to_datetime(alldf['time'])

        # Calculate duration until the next activity
        alldf['time'] = alldf['time'].shift(-1) - alldf['time']

        # Optional: convert to seconds
        alldf['time'] = alldf['time'].dt.total_seconds()
        #activitydf['time'] = pd.to_timedelta(activitydf['time'], unit='s')

        counts = originalDf['activity_block'].value_counts().sort_index().reset_index(drop=True)
        alldf['activity_num'] = counts

        alldf = originalDf.copy()

        # Identify activity blocks
        alldf['activity_block'] = (alldf['activity'] != alldf['activity'].shift()).cumsum()

        # Keep only transitions
        alldf = alldf[alldf['activity'] != alldf['activity'].shift()].reset_index(drop=True)

        # Create datetime from date and time (start of activity)
        alldf['datetime'] = pd.to_datetime(alldf['date'] + ' ' + alldf['time'])

        # Shift to get duration between transitions
        alldf['duration'] = alldf['datetime'].shift(-1) - alldf['datetime']
        alldf['duration_sec'] = alldf['duration'].dt.total_seconds()

        # Extract day for grouping
        alldf['day'] = alldf['datetime'].dt.date

        # Group by day and sum duration
        daily_activity = alldf.groupby('day')['duration_sec'].sum().reset_index()

        # Optional: convert to minutes
        daily_activity['duration_min'] = daily_activity['duration_sec'] / 60

        chart = alt.Chart(daily_activity).mark_bar().encode(
            x=alt.X('day:T', title='Date'),
            y=alt.Y('duration_min:Q', title='Total Activity'),
            tooltip=['day', 'duration_min']
        ).properties(
            title='Total Activity per Day',
            width=700,
            height=400
        )

        st.altair_chart(chart, use_container_width=True)

