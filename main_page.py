import pandas as pd
import plotly.express as px
import streamlit as st
import plotly.graph_objs as go
import requests
############################            STREAMLIT LAYOUT             ##########################################################
st.set_page_config(layout="wide",page_title="Current State of EEG-based Neuromonitoring - Results from an international survey")


def extract_questions(data_frame,name_frame,questions2extract):
    data_frame = data_frame[questions2extract]
    name_frame = name_frame.loc[name_frame['Question ID'].isin(questions2extract)]
    names = name_frame.iloc[:,1]
    data_frame = data_frame.iloc[1:] # remove the first row, since it does not contain information
    data_frame.columns = names      # assign new names (for plotting)
    return data_frame

def calculate_percentages(data_frame,sort_name,label_order):
    # Calculate the percentage of each answer
    percentage_df = data_frame.apply(lambda x: x.value_counts(normalize=True) * 100)
    percentage_df = percentage_df.round(2)
    # Transpose the DataFrame for plotting
    percentage_df = percentage_df.T
    percentage_df = percentage_df.sort_values(by = sort_name, ascending=True)
    percentage_df.fillna(0, inplace=True)
    percentage_df = percentage_df[label_order]
    return percentage_df

def create_boxchart(percentage_frame,question_title,ax_title,bar_colors):
    fig = px.bar(percentage_frame, barmode='stack',orientation='h', text_auto=True,color_discrete_sequence=bar_colors,opacity=0.8)
    fig.update_layout(
    title=question_title,
    xaxis_title=ax_title,
    yaxis=dict(title='',tickfont=dict(size=15)),
    )
    return fig

def create_boxchart_overlay(data_frame):
    # Create individual bar traces
    axis_name = data_frame["Category"]
    current_data = [data_frame["Ist"]]
    target_data = [data_frame["Soll"]]
    trace1 = go.Bar(x=[axis_name], y=current_data, name='Ist', opacity=1,width=[0.2, 0.6, 0.2],text=current_data)
    trace2 = go.Bar(x=[axis_name], y=target_data, name='Soll', opacity=0.5,width=[0.3, 0.6, 0.2],text=target_data)
    # Create a figure and add traces
    fig = go.Figure(data=[trace1, trace2])
    # Update layout to overlay mode
    fig.update_layout(barmode='overlay',yaxis_range=[0,100])
    return fig

def prepare_chart(data_frame,name_frame,questions2extract,value_map,value_idx,label_order,question_title,ax_title):
    current_question = extract_questions(data_frame,name_frame,questions2extract)
    current_question = current_question.replace(value_map)
    question_in_percentage = calculate_percentages(current_question,value_map[value_idx],label_order)
    fig = create_boxchart(question_in_percentage,question_title,ax_title)
    return fig

def reformat_series(series):
    """
    Reformats the given Pandas Series by splitting the index into 'Category' and 'Type' (Soll/Ist),
    pivoting the Series to align Soll and Ist values, and sorting based on Soll values and
    the difference between Soll and Ist.

    :param series: pandas Series with the index as 'Question Text' and values.
    :return: Reformatted DataFrame
    """
    # Convert the series into a DataFrame
    df = series.reset_index()
    df.columns = ['Question Text', 'Value']

    # Splitting the "Question Text" using standard Python string method
    df['Category'] = df['Question Text'].apply(lambda x: ' '.join(x.rsplit(' ')[:-1]))
    df['Type'] = df['Question Text'].apply(lambda x: x.rsplit(' ')[-1])

    # Pivoting the DataFrame to have Soll and Ist values in separate columns
    pivot_df = df.pivot(index='Category', columns='Type', values='Value').reset_index()

    # Calculating the difference between Soll and Ist
    pivot_df['Difference'] = abs(pivot_df['Soll'] - pivot_df['Ist'])

    # Sorting first by 'Soll' in descending order and then by 'Difference' in descending order
    sorted_df = pivot_df.sort_values(by=['Soll', 'Difference'], ascending=[False, False])

    return sorted_df


@st.cache_data
def load_dataframe(f):
    raw_data = pd.read_excel(f[0])
    question_names = pd.read_excel(f[1])
    return raw_data, question_names

# Load the dataset
survey_filenames = st.sidebar.file_uploader("Choose a CSV file", accept_multiple_files=True)
if len(survey_filenames) == 0:
    survey_filenames = []
    survey_filenames.append("https://github.com/JulianOstertag/Neuromonitoring_Survey/raw/main/Completed_Surveys.xlsx")
    survey_filenames.append("https://github.com/JulianOstertag/Neuromonitoring_Survey/raw/main/Question_Names.xlsx")
raw_data, question_names = load_dataframe(survey_filenames)
value_map = {1: '<1', 2: '1-5', 3: '>5'}
raw_data["Q2"] = raw_data['Q2'].replace(value_map)
replacement_dict = {
    '1': 'BIS',
    '2': 'GE Entropy',
    '3': 'SedLine',
    '4': 'qCon',
    '5': 'Sonstige',
}
raw_data["Q3"] = raw_data['Q3'].replace(replacement_dict, regex=True)
raw_data_copy = raw_data.copy()
###################################   Streamlit code   ########################
# Sidebar
st.sidebar.header('Filter Optionen')
# Filter by Category (using a multiselect box)
filter_by_experience = st.sidebar.multiselect('Filter nach Berufserfahrung', ['<1','1-5','>5'])
filter_by_device = st.sidebar.multiselect('Filter nach Monitor', ['SedLine','BIS','GE Entropy','qCon', 'Sonstige'])
if st.sidebar.button('Filter'):
    regex_pattern_device = '|'.join(filter_by_device) 
    regex_pattern_experience = '|'.join(filter_by_experience) 
    device_mask = raw_data_copy['Q3'].str.contains(regex_pattern_device)
    experience_mask = raw_data_copy['Q2'].str.contains(regex_pattern_experience)
    data_frame_mask = device_mask & experience_mask
    raw_data_copy = raw_data_copy[data_frame_mask]



################################      Question 4       #############################################################
question_title = "EEG basierte Monitoring Geräte..."
ax_title = 'Percentage [%]'
questions = ["Q4_1","Q4_2", "Q4_3", "Q4_4", "Q4_5", "Q4_6", "Q4_7", "Q4_8"]
current_question = extract_questions(raw_data_copy,question_names,questions)
# Replace values with their meanings
value_map = {1: 'Stimme nicht zu', 2: 'Neutral', 3: 'Stimme zu'}
label_order = ["Stimme zu","Neutral","Stimme nicht zu"]
current_question = current_question.replace(value_map)
# Calculate the percentage of each answer
question_in_percentage = calculate_percentages(current_question,value_map[3],label_order)
bar_cols = ["#C7D97D", "#165DB1", "#EF9067"]
fig = create_boxchart(question_in_percentage,question_title,ax_title,bar_cols)


tab1, tab2,tab3,tab4,tab5 = st.tabs(["Status Quo","Wünsche","Einsatzfelder","Features",'Soll - Ist Analyse'])
tab1.plotly_chart(fig, use_container_width=True)    
################################      Question 5       #############################################################
question_title = "Um Neuromonitoring im klinischen Alltag anzuwenden wäre es wichtig, dass..."
ax_title = 'Percentage [%]'
questions = ["Q5_1","Q5_2", "Q5_3", "Q5_4", "Q5_5"]
current_question = extract_questions(raw_data_copy,question_names,questions)
# Replace values with their meanings
value_map = {1: 'Stimme nicht zu', 2: 'Neutral', 3: 'Stimme zu'}
label_order = ["Stimme zu","Neutral","Stimme nicht zu"]
current_question = current_question.replace(value_map)
# Calculate the percentage of each answer
question_in_percentage = calculate_percentages(current_question,value_map[3],label_order)
fig = create_boxchart(question_in_percentage,question_title,ax_title,bar_cols)
tab2.plotly_chart(fig, use_container_width=True)

################################      Question 6       #############################################################
question_title = "Der Einsatz von EEG basierten Monitoring Geräten führt aktuell dazu, dass..."
ax_title = 'Percentage [%]'
questions = ["Q6_1","Q6_2", "Q6_3", "Q6_4", "Q6_5","Q6_6", "Q6_7"]
current_question = extract_questions(raw_data_copy,question_names,questions)
# Replace values with their meanings
value_map = {1: 'Stimme nicht zu', 2: 'Neutral', 3: 'Stimme zu'}
label_order = ["Stimme zu","Neutral","Stimme nicht zu"]
current_question = current_question.replace(value_map)
# Calculate the percentage of each answer
question_in_percentage = calculate_percentages(current_question,value_map[3],label_order)
fig = create_boxchart(question_in_percentage,question_title,ax_title,bar_cols)
tab3.plotly_chart(fig, use_container_width=True)
################################      Features       #############################################################
question_title = "Feature Bewertung"
ax_title = 'Percentage [%]'
questions = ["Q11","Q12", "Q13", "Q14", "Q15"]
current_question = extract_questions(raw_data_copy,question_names,questions)
# Replace values with their meanings
value_map = {34: 'Überhaupt nicht interessant', 35: 'Einigermaßen interessant', 36: 'Interessant', 37: 'Sehr interessant',38: 'Extrem interessant'}
label_order = ["Extrem interessant","Sehr interessant","Interessant","Einigermaßen interessant","Überhaupt nicht interessant"]
current_question = current_question.replace(value_map)
# Calculate the percentage of each answer
question_in_percentage = calculate_percentages(current_question,value_map[38],label_order)
bar_cols = ["#C7D97D", "#165DB1","#E3EEFA","#C2D7EF", "#EF9067"]
fig = create_boxchart(question_in_percentage,question_title,ax_title,bar_cols)
tab4.plotly_chart(fig, use_container_width=True)

################################      target and Current Values      #############################################################
question_title = "Feature Bewertung"
ax_title = 'Percentage [%]'
questions = ["Q7_1","Q7_2", "Q7_3", "Q7_4", "Q8_1","Q8_2", "Q8_3","Q8_4","Q9_1","Q9_2", "Q9_3", "Q9_4", "Q10_1","Q10_2", "Q10_3","Q10_4"]
current_question = extract_questions(raw_data_copy,question_names,questions)
median_question = current_question.median(axis = 0)
current_question = reformat_series(median_question)
with tab5:
    cnt = 0
    col1 = st.columns(4)
    for i in range(0,4,1):
        fig = create_boxchart_overlay(current_question.iloc[i,:])
        col1[cnt].plotly_chart(fig, use_container_width=True)
        cnt = cnt+1

with tab5:
    cnt = 0
    col2 = st.columns(4)
    for i in range(4,8,1):
        fig = create_boxchart_overlay(current_question.iloc[i,:])
        col2[cnt].plotly_chart(fig, use_container_width=True)
        cnt = cnt+1